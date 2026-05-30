#!/usr/bin/env python3
"""v0.17 — Operating Loop MVP Runner.

Manual execution mode. Supports --dry-run (preview only) and --once (execute).

Usage:
    python3 scripts/run_operating_loop.py --dry-run
    python3 scripts/run_operating_loop.py --once
    python3 scripts/run_operating_loop.py --once --force
    python3 scripts/run_operating_loop.py --once --scan-pending

Options:
    --dry-run        Preview what would happen without executing anything.
    --once           Execute due scheduled tasks once.
    --force          Skip dedup check (allow same-day re-runs).
    --scan-pending   Also scan pending Work Orders (default: False).
"""

import argparse
import sys
import os
from datetime import date

# Ensure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.scheduler import (
    load_scheduled_work_orders,
    get_due_tasks,
    build_scheduled_reason,
    already_ran_today,
    ScheduledWorkOrder,
)
from app.services.runtime_health import check_all, check_runtime
from app.services.budget_guard import check_work_order, load_policy
from app.services.failure_policy import FailureAction, classify
from app.services.cost_summary import scan_all
from app.services.ceo_brief import generate_brief, save_brief
from app.services.work_order_executor import execute_work_order
from app.database import get_sync_session
from app.models.work_order import WorkOrder


def _generate_wo_id() -> str:
    import uuid
    return f"WO-{uuid.uuid4().hex[:8].upper()}"


def _format_dry_run(task: ScheduledWorkOrder, force: bool = False) -> str:
    """Format a single task for dry-run display."""
    deduped = already_ran_today(task.id) if not force else False
    lines = [
        f"  ┌─ {task.id}",
        f"  ├─ Label:       {task.label}",
        f"  ├─ Type:        {task.task_type}",
        f"  ├─ Skill:       {task.skill_id}",
        f"  ├─ Agent:       {task.agent}",
        f"  ├─ Risk:        {task.risk_level}",
        f"  ├─ Exec Mode:   {task.execution_mode}",
        f"  └─ Already ran: {'✅ yes' if deduped else '❌ no'}",
    ]
    return "\n".join(lines)


def run_dry_run(today: date, force: bool = False) -> bool:
    """Dry run mode: show what would happen without executing anything.

    Returns:
        True if any tasks would run.
    """
    print("=" * 60)
    print("  AI Company OS — Operating Loop (DRY RUN)")
    print(f"  Date: {today.isoformat()}")
    print("=" * 60)
    print()

    due = get_due_tasks(today, force=force)
    if not due:
        print("📭 No scheduled tasks due today.")
        return False

    print(f"📋 {len(due)} task(s) due today:\n")
    for task in due:
        print(_format_dry_run(task, force=force))
        print()

    # Health preview
    print("\n📡 Runtime Health (current):")
    health_results = check_all()
    for name, r in sorted(health_results.items()):
        icon = "✅" if r.status == "healthy" else "❌"
        print(f"  {icon} {name}: {r.status}")

    # Cost preview
    cost = scan_all()
    print(f"\n💰 Current cost: {cost.total_tokens:,} tokens, ${cost.total_estimated_cost:.4f}")

    # Budget preview
    print(f"\n🔒 Budget policy loaded: {load_policy().get('default', {}).get('max_tokens_per_work_order', '?')} tokens/WO")

    print()
    print(f"💼 CEO Brief will be saved to: reports/ceo-briefs/DRY-RUN-{today.isoformat()}.md")
    print("=" * 60)
    print("  No Work Orders were created or executed.")
    print("=" * 60)

    # Still generate a dry-run CEO Brief for feedback
    brief = generate_brief(
        scheduled_id="dry-run",
        today=today,
        dry_run=True,
        execution_results=[],
    )
    path = save_brief(brief, today, dry_run=True)
    return True


def run_once(today: date, force: bool = False) -> bool:
    """Execute mode: run due tasks and generate CEO Brief.

    Returns:
        True if at least one task was executed.
    """
    print("=" * 60)
    print("  AI Company OS — Operating Loop (ONCE)")
    print(f"  Date: {today.isoformat()}")
    print(f"  Force: {'on' if force else 'off'}")
    print("=" * 60)
    print()

    due = get_due_tasks(today, force=force)
    if not due:
        print("📭 No scheduled tasks due today.")
        return False

    print(f"📋 {len(due)} task(s) to execute:\n")
    for task in due:
        print(f"  - {task.id} ({task.label})")
    print()

    # ── Step 1: Health Check ──
    print("━" * 50)
    print("📡 Step 1: Runtime Health Check")
    health_results = check_all()
    all_healthy = all(r.status == "healthy" for r in health_results.values())
    any_unhealthy = [name for name, r in health_results.items() if r.status != "healthy"]

    for name, r in sorted(health_results.items()):
        icon = "✅" if r.status == "healthy" else "❌"
        print(f"  {icon} {name}: {r.status}")

    if not all_healthy:
        print(f"  ⚠️ Unhealthy: {', '.join(any_unhealthy)}")
        print("  → Skipping execution. Fix unhealthy runtimes first.")
        brief = generate_brief(
            scheduled_id="operating-loop",
            today=today,
            execution_results=[],
            failures=[{"message": f"Runtime(s) unhealthy: {', '.join(any_unhealthy)}"}],
        )
        save_brief(brief, today)
        return False
    print()

    # ── Step 2: Execute each due task ──
    print("━" * 50)
    print("⚡ Step 2: Execute Scheduled Work Orders")

    results = []
    failures = []
    budget_warnings = []

    for task in due:
        print(f"\n  → Creating Work Order for: {task.id}")

        # Budget check before creating
        print(f"  → Budget check (max 20k tokens default)...")
        budget_result = check_work_order(total_tokens=0, skill_id=task.skill_id)
        # Can't know exact tokens upfront; check on the total system usage
        cost = scan_all()
        daily_check = check_work_order(total_tokens=cost.total_tokens, skill_id=task.skill_id)
        if not daily_check.passed:
            for v in daily_check.violations:
                msg = v.message
                print(f"  ⚠️ Budget warning: {msg[:100]}")
                budget_warnings.append(msg)

        # Create Work Order
        wo_id = _generate_wo_id()
        session = get_sync_session()
        try:
            reason = build_scheduled_reason(task.id, today)
            wo = WorkOrder(
                work_order_id=wo_id,
                skill_id=task.skill_id,
                task_type=task.task_type,
                route_reason=reason,
                risk_level=task.risk_level,
                execution_mode=task.execution_mode,
                assigned_agent=task.agent,
                input_context=task.input_context,
                status="routed",  # Pre-routed = ready for execute
            )
            session.add(wo)
            session.commit()
            print(f"  ✅ Created: {wo_id} (status=routed)")
        except Exception as e:
            print(f"  ❌ Failed to create Work Order: {e}")
            failures.append({"message": f"Create WO failed for {task.id}: {e}"})
            continue
        finally:
            session.close()

        # Execute
        print(f"  → Executing: {wo_id}")
        try:
            result = execute_work_order(wo_id)
            # Check for execution errors at top level
            if "error" in result and result.get("work_order", {}).get("status") == "failed":
                # Apply failure policy
                wo_data = result.get("work_order", {})
                fp = classify(
                    task_type=task.task_type,
                    risk_level=task.risk_level,
                    attempt_count=wo_data.get("attempt_count", 1),
                    executor_result={
                        "executor_type": wo_data.get("execution_mode", "unknown"),
                        "status": "error",
                        "error": result.get("error", "Unknown execution error"),
                    },
                )
                failure_entry = {
                    "work_order_id": wo_id,
                    "task_id": task.id,
                    "failure_code": fp.code.value,
                    "action": fp.action.value,
                    "message": f"[{fp.action.value}] {fp.reason}",
                }
                failures.append(failure_entry)
                print(f"  ⚠️ Failed: {wo_id} → {fp.action.value} ({fp.reason[:80]})")
            else:
                wo_status = result.get("work_order", {}).get("status", "?")
                print(f"  ✅ Done: {wo_id} → status={wo_status}")
            results.append(result)
        except Exception as e:
            print(f"  ❌ Execute error: {e}")
            failures.append({"message": f"Execute error for {wo_id}: {e}"})
            continue

    # ── Step 3: Generate CEO Brief ──
    print()
    print("━" * 50)
    print("💼 Step 3: Generate CEO Brief")

    brief = generate_brief(
        scheduled_id="operating-loop",
        today=today,
        execution_results=results,
        failures=failures,
        budget_warnings=budget_warnings,
    )
    path = save_brief(brief, today)

    print()
    print("=" * 60)
    print(f"  ✅ Operating Loop complete.")
    print(f"  Work Orders created: {len(results)}")
    print(f"  Failed: {len(failures)}")
    print(f"  Budget warnings: {len(budget_warnings)}")
    print(f"  CEO Brief: {path}")
    print("=" * 60)
    return True


# ── Main ──

def parse_args():
    parser = argparse.ArgumentParser(
        description="AI Company OS — Operating Loop MVP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview what would happen without executing anything.")
    parser.add_argument("--once", action="store_true",
                        help="Execute due scheduled tasks once.")
    parser.add_argument("--force", action="store_true",
                        help="Skip dedup check (allow same-day re-runs).")
    parser.add_argument("--scan-pending", action="store_true",
                        help="Also scan pending Work Orders (default: False).")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if not args.dry_run and not args.once:
        print("⚠️  Must specify --dry-run or --once")
        sys.exit(1)

    today = date.today()
    print(f"AI Company OS v0.17 Operating Loop — {today.isoformat()}")
    print()

    if args.dry_run:
        ran = run_dry_run(today, force=args.force)
    elif args.once:
        ran = run_once(today, force=args.force)

    if args.scan_pending:
        print()
        print("📝 --scan-pending: scanning pending Work Orders (not yet implemented in v0.17)")

    sys.exit(0 if ran else 1)
