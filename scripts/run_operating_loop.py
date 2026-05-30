#!/usr/bin/env python3
"""v0.17 — Operating Loop MVP Runner.

Manual execution mode. Supports --dry-run (preview only) and --once (execute).

Usage:
    python3 scripts/run_operating_loop.py --dry-run
    python3 scripts/run_operating_loop.py --once
    python3 scripts/run_operating_loop.py --once --force
    python3 scripts/run_operating_loop.py --once --wait-results --timeout 120
    python3 scripts/run_operating_loop.py --once --scan-pending

Options:
    --dry-run        Preview what would happen without executing anything.
    --once           Execute due scheduled tasks once.
    --force          Skip dedup check (allow same-day re-runs).
    --wait-results   Wait for worker to complete Work Orders before generating Brief.
    --timeout N      Max seconds for --wait-results (default: 120).
    --scan-pending   Also scan pending Work Orders (default: False).
"""

import argparse
import sys
import os
from datetime import date

# Ensure backend/ is CWD for correct DB path resolution
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
_BACKEND_DIR = os.path.join(_PROJECT_ROOT, "backend")
os.chdir(_BACKEND_DIR)

# Ensure the backend package is importable from the correct directory
sys.path.insert(0, _BACKEND_DIR)

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
from app.services.run_ledger_service import record_and_register
from app.database import get_sync_session
from app.models.work_order import WorkOrder
from app.config import DATABASE_PATH, BACKEND_ROOT

# ── Startup diagnostics ──
print(f"[operating-loop] DB: {DATABASE_PATH}")
print(f"[operating-loop] Backend: {BACKEND_ROOT}")

# Check for stale DB files at project root (legacy dual-DB detection)
_LEGACY_DB = os.path.join(os.path.dirname(BACKEND_ROOT), "data", "ai_company_os.db")
if os.path.exists(_LEGACY_DB):
    print(f"⚠️  [operating-loop] WARNING: Legacy DB detected at {_LEGACY_DB}")
    print(f"   This DB is NOT being used. Remove it to avoid confusion.")
print()


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


def run_once(today: date, force: bool = False,
             wait_results: bool = False, wait_timeout: int = 120) -> bool:
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

    # Pre-run snapshot for budget scope
    cost_before = scan_all()
    current_run_tokens_before = cost_before.total_tokens

    for task in due:
        print(f"\n  → Creating Work Order for: {task.id}")

        # Budget check before creating
        print(f"  → Budget check...")
        # Check per-WO budget (pre-check: current total is 0, won't fire)
        wo_check = check_work_order(total_tokens=0, skill_id=task.skill_id, scope="per_work_order")
        # Lifetime budget — display only, never triggers warning
        lifetime_check = check_work_order(total_tokens=current_run_tokens_before, skill_id=task.skill_id, scope="lifetime")

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

    # ── Step 2.5: Wait for results (--wait-results mode) ──
    pending_ids = []
    for r in results:
        wo_data = r.get("work_order", {})
        if wo_data.get("status") in ("in_progress", "routed"):
            pending_ids.append(wo_data["work_order_id"])

    if wait_results and pending_ids:
        print()
        print("━" * 50)
        print(f"⏳ Step 2.5: Waiting for {len(pending_ids)} WO(s) to complete (timeout={wait_timeout}s)")

        # Run the worker to process pending tasks
        worker_script = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "bin", "openclaw_worker.py"
        )
        import subprocess
        worker_cmd = [sys.executable, worker_script, "--all", "--call-backend",
                      "--backend-url", "http://localhost:8001"]
        print(f"  → Running worker: {' '.join(worker_cmd)}")
        worker_result = subprocess.run(worker_cmd, capture_output=True, text=True, timeout=wait_timeout)
        for line in worker_result.stdout.strip().split("\n"):
            print(f"  {line}")
        if worker_result.stderr:
            print(f"  ⚠️ Worker stderr: {worker_result.stderr[:200]}")

        # Poll WO status in DB
        import time as time_module
        deadline = time_module.time() + (wait_timeout - 10)  # reserve 10s for Brief
        completed_ids = []
        attempted_ids = []
        for wo_id in pending_ids:
            while time_module.time() < deadline:
                session = get_sync_session()
                try:
                    wo = session.query(WorkOrder).filter_by(work_order_id=wo_id).first()
                    if wo and wo.status == "completed":
                        completed_ids.append(wo_id)
                        print(f"  ✅ {wo_id} → completed")
                        break
                    elif wo and wo.status in ("failed",):
                        print(f"  ❌ {wo_id} → failed")
                        break
                finally:
                    session.close()
                time_module.sleep(3)
            else:
                attempted_ids.append(wo_id)
                print(f"  ⏰ {wo_id} → timeout_pending (not yet completed within timeout)")

        print(f"  Results: {len(completed_ids)} completed, {len(attempted_ids)} pending/timeout")

        # Re-read completed results from DB for the Brief
        results = []
        for wo_id in pending_ids:
            session = get_sync_session()
            try:
                wo = session.query(WorkOrder).filter_by(work_order_id=wo_id).first()
                if wo:
                    results.append({
                        "work_order": wo.to_dict(),
                        "execution_result": {},
                    })
            finally:
                session.close()

    # ── Post-execution budget check (current run scope) ──
    cost_after = scan_all()
    current_run_tokens = cost_after.total_tokens - current_run_tokens_before
    run_budget_check = check_work_order(
        total_tokens=current_run_tokens,
        scope="current_run"
    )
    if not run_budget_check.passed:
        for v in run_budget_check.violations:
            msg = v.message
            print(f"  ⚠️ Budget warning (current run): {msg[:100]}")
            budget_warnings.append(msg)
    else:
        print(f"  ✅ Run budget OK ({current_run_tokens:,} tokens this run)")

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
        wait_results=wait_results,
        completed_after_wait=(wait_results and len(attempted_ids) == 0) if wait_results else False,
    )
    path = save_brief(brief, today)
    brief_rel = os.path.relpath(path, _PROJECT_ROOT)
    r = record_and_register(
        event_type="brief_generated",
        asset_type="ceo_brief",
        source_type="file",
        source_id=brief_rel,
        path=path,
        summary=f"CEO Brief generated: {today}",
        actor="operating_loop",
    )
    if r["event_recorded"]:
        print(f"  📋 Run Ledger: brief_generated recorded")
    if r["asset_id"]:
        print(f"  📦 Asset Registry: ceo_brief asset {r['asset_id']}")

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
    parser.add_argument("--wait-results", action="store_true",
                        help="Wait for worker to complete Work Orders before generating CEO Brief.")
    parser.add_argument("--timeout", type=int, default=120,
                        help="Max seconds to wait for --wait-results (default: 120).")
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
        ran = run_once(today, force=args.force, wait_results=args.wait_results, wait_timeout=args.timeout)

    if args.scan_pending:
        print()
        print("📝 --scan-pending: scanning pending Work Orders (not yet implemented in v0.17)")

    sys.exit(0 if ran else 1)
