#!/usr/bin/env python3
"""
v0.30 — Workflow Runner CLI

Orchestrates multi-step Work Orders via explicit template-driven workflows.
Every step respects Founder approval, Policy Resolver, and existing Work Order lifecycle.

Usage:
    python3 scripts/workflow_runner.py create --template decision_followup_workflow [--context "..."]
    python3 scripts/workflow_runner.py status <workflow_id>
    python3 scripts/workflow_runner.py next <workflow_id>
    python3 scripts/workflow_runner.py resolve <workflow_id> <step_id>
    python3 scripts/workflow_runner.py skip <workflow_id> <step_id>
    python3 scripts/workflow_runner.py cancel <workflow_id>
"""

import argparse
import json
import os
import sys
import yaml
from datetime import datetime
from typing import Optional

# ── Paths ─────────────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
_BACKEND_DIR = os.path.join(_PROJECT_ROOT, "backend")
if os.path.isdir(_BACKEND_DIR):
    sys.path.insert(0, _BACKEND_DIR)

from workflow_helpers import (
    load_template,
    generate_workflow_id,
    generate_draft_id,
    record_ledger_event,
    record_and_register_asset,
    query_asset_by_source,
    write_draft_with_front_matter,
    read_draft_metadata,
    list_templates,
)


# ── Policy Check ──────────────────────────────────────────────

def _policy_check(actor: str, action: str, source_id: str = "", summary: str = "", mode: str = "advisory") -> dict:
    """Run policy resolver check. Returns decision dict or empty (no-op) on failure."""
    try:
        from scripts.policy_resolver import check_and_record
        return check_and_record(
            actor_id=actor,
            action=action,
            source_id=source_id,
            summary=summary,
            mode=mode,
            record=True,
        )
    except ImportError:
        return {}
    except Exception as e:
        print(f"  ⚠️  Policy check unavailable: {e}")
        return {}


# ── Run Ledger Query ──────────────────────────────────────────

def _get_events_by_source(source_id: str) -> list[dict]:
    """Query Run Ledger events by source_id (workflow_id)."""
    try:
        from app.database import get_sync_session
        from app.models.run_ledger_event import RunLedgerEvent
        session = get_sync_session()
        events = (
            session.query(RunLedgerEvent)
            .filter(RunLedgerEvent.source_id == source_id)
            .order_by(RunLedgerEvent.timestamp.asc())
            .all()
        )
        return [
            {
                "event_type": e.event_type,
                "source_id": e.source_id,
                "summary": e.summary,
                "metadata": json.loads(e.metadata_json) if e.metadata_json else {},
                "created_at": str(e.timestamp),
            }
            for e in events
        ]
    except Exception as ex:
        print(f"  ⚠️  Run Ledger query unavailable: {ex}")
        return []


# ── Create ────────────────────────────────────────────────────

def cmd_create(template_name: str, context: str = "") -> Optional[str]:
    """Create a new workflow: load template, generate ID, write events, generate step 1 Draft.

    Returns workflow_id on success, None on failure.
    """
    # ── Load template ──
    try:
        tpl = load_template(template_name)
    except FileNotFoundError:
        print(f"  ❌ Template not found: {template_name}")
        print(f"     Available: {', '.join(list_templates())}")
        return None
    except yaml.YAMLError as e:
        print(f"  ❌ Template YAML error: {e}")
        return None

    steps = tpl.get("steps", [])
    if not steps:
        print(f"  ❌ Template '{template_name}' has no steps")
        return None

    wf_meta = tpl.get("workflow", {})
    wf_id = generate_workflow_id()

    # ── Policy check ──
    policy = _policy_check(
        actor="workflow-runner",
        action="create_workflow",
        source_id=wf_id,
        summary=f"Create workflow {wf_id} from template {template_name}",
    )
    if policy.get("verdict") == "BLOCKED":
        print(f"  🚫 Policy blocked: create_workflow action not allowed")
        return None

    # ── Write workflow_created event ──
    workflow_data = {
        "workflow_id": wf_id,
        "template": template_name,
        "status": "active",
        "total_steps": len(steps),
        "current_step_index": 0,
        "created_via": "cli",
        "context_summary": context or "(none)",
    }
    record_and_register_asset(
        event_type="workflow_created",
        source_type="workflow_cli",
        source_id=wf_id,
        summary=f"Workflow {wf_id} created from template '{template_name}' ({len(steps)} steps)",
        asset_type="workflow_plan",
        path=f"workflow://{wf_id}",
        metadata=workflow_data,
    )

    # ── Generate Step 1 Draft ──
    step_1 = steps[0]
    draft_id = _generate_step_draft(wf_id, template_name, steps, step_1, 0, context)

    # ── Write workflow_step_created event ──
    record_ledger_event(
        event_type="workflow_step_created",
        source_type="workflow_cli",
        source_id=wf_id,
        summary=f"Step 1 '{step_1['step_id']}' draft generated ({draft_id})",
        metadata={
            "workflow_id": wf_id,
            "step_id": step_1["step_id"],
            "draft_id": draft_id,
            "step_index": 0,
        },
    )

    print(f"\n  ✅ Workflow created: {wf_id}")
    print(f"     Template:       {template_name}")
    print(f"     Steps:          {len(steps)}")
    print(f"     Step 1 Draft:   reports/work-order-drafts/{draft_id}.md")
    print(f"     Context:        {context or '(none)'}")
    print(f"\n  ℹ️  Next: python3 scripts/workflow_runner.py next {wf_id}")
    print(f"     (after step 1 completed)")

    return wf_id


def _generate_step_draft(
    wf_id: str,
    template_name: str,
    all_steps: list,
    step: dict,
    step_index: int,
    context: str = "",
    source_asset_summary: str = "",
) -> str:
    """Generate a Draft for a specific workflow step.

    Returns the draft_id.
    """
    draft_id = generate_draft_id()
    step_id = step["step_id"]
    total_steps = len(all_steps)

    # Build depends_on list for front matter
    depends_on = []
    for dep in step.get("depends_on", []):
        depends_on.append({
            "step": dep["step"],
            "consumes_asset": dep.get("consumes_asset"),
        })

    # Build outputs list for front matter
    outputs = []
    for out in step.get("outputs", []):
        outputs.append({
            "asset_type": out["asset_type"],
            "required": out.get("required", False),
            "status": "pending",
        })

    # Build draft body
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    body = f"""# Work Order Draft — {wf_id} / {step_id}

**Draft ID:** {draft_id}
**Workflow ID:** {wf_id}
**Step:** {step_id} ({step_index + 1}/{total_steps})
**Template:** {template_name}
**Created:** {now}
**Generated By:** workflow-runner

---

## Step Description

{step.get('description', '')}

"""

    if source_asset_summary:
        body += f"""## Source Context

{source_asset_summary}

---

"""

    if context:
        body += f"""## Founder Context

{context}

---

"""

    body += f"""## Auto-filled Title

{context or step.get('description', '')}

---

## Founder To Fill

**Suggested Task Type:**
```
{step.get('task_type', 'TBD')}
```

**Proposed Prompt:**
```
Based on {wf_id} step '{step_id}': {context or step.get('description', '')}
```

**Expected Output:**
```
TODO: Founder to fill
```

---

## Founder Confirmation

- [ ] approve_create_work_order (确认创建 Work Order)
- [ ] edit_required (需要修改)
- [ ] dismiss (放弃此草稿)

---

## Notes

_Draft generated by workflow runner for {wf_id} / {step_id}._

---

_draft_status: draft_
"""

    write_draft_with_front_matter(
        draft_id=draft_id,
        workflow_id=wf_id,
        step_id=step_id,
        template_name=template_name,
        step_index=step_index,
        total_steps=total_steps,
        depends_on=depends_on,
        outputs=outputs,
        body=body,
    )

    return draft_id


# ── Status ────────────────────────────────────────────────────

def cmd_status(workflow_id: str) -> None:
    """Show workflow status by querying Run Ledger events."""
    events = _get_events_by_source(workflow_id)
    if not events:
        print(f"  ❌ Workflow not found: {workflow_id}")
        print(f"     No Run Ledger events for this ID.")
        return

    # Parse workflow metadata from events
    wf_event = next((e for e in events if e["event_type"] == "workflow_created"), None)
    if not wf_event:
        print(f"  ❌ No workflow_created event for {workflow_id}")
        return

    meta = wf_event.get("metadata", {})
    template = meta.get("template", "")
    if not template:
        # Fallback: parse from summary
        summary = wf_event.get("summary", "")
        if "from template '" in summary:
            template = summary.split("from template '")[1].split("'")[0]
    total_steps = meta.get("total_steps", "?")

    # Load template to get step names
    try:
        tpl = load_template(template)
        steps_def = tpl.get("steps", [])
    except (FileNotFoundError, yaml.YAMLError):
        steps_def = []

    print(f"\n  📋 Workflow Status: {workflow_id}")
    print(f"  {'=' * 50}")
    print(f"  Template:  {template}")
    print(f"  Steps:     {total_steps}")
    print()

    # Show each step status
    for idx in range(int(total_steps) if isinstance(total_steps, int) else 0):
        step_def = steps_def[idx] if idx < len(steps_def) else None
        step_id = step_def["step_id"] if step_def else f"step_{idx + 1}"

        # Find events for this step
        step_created = next(
            (e for e in events if e.get("metadata", {}).get("step_id") == step_id),
            None,
        )
        step_completed = next(
            (e for e in events
             if e["event_type"] == "workflow_step_completed"
             and e.get("metadata", {}).get("step_id") == step_id),
            None,
        )
        step_skipped = next(
            (e for e in events
             if e["event_type"] == "workflow_step_skipped"
             and e.get("metadata", {}).get("step_id") == step_id),
            None,
        )

        if step_skipped:
            icon, status = "⏭️", "skipped"
        elif step_completed:
            icon, status = "✅", "completed"
        elif step_created:
            icon, status = "📄", "draft_ready"
        else:
            icon, status = "⏳", "pending"

        action_class = step_def["action_class"] if step_def else "?"
        print(f"  {icon}  {step_id} ({action_class}) — {status}")

    # Check if cancelled
    cancelled = next(
        (e for e in events if e["event_type"] == "workflow_cancelled"), None
    )
    all_completed = all(
        any(
            e["event_type"] == "workflow_step_completed"
            and e.get("metadata", {}).get("step_id", "") == s["step_id"]
            for e in events
        )
        for s in steps_def
        if s.get("step_id")
    )

    if cancelled:
        print(f"\n  🚫  Status: CANCELLED")
    elif all_completed:
        print(f"\n  ✅  Status: COMPLETED")
    else:
        print(f"\n  🔄  Status: ACTIVE")

    print()


# ── Next ──────────────────────────────────────────────────────

def cmd_next(workflow_id: str) -> None:
    """Advance workflow to next step.

    1. Find current step from Run Ledger events
    2. Check dependency completion (completion_criteria)
    3. Read asset with 3-layer fallback
    4. Generate next step Draft with context
    """
    events = _get_events_by_source(workflow_id)
    if not events:
        print(f"  ❌ Workflow not found: {workflow_id}")
        return

    # Get workflow metadata
    wf_event = next((e for e in events if e["event_type"] == "workflow_created"), None)
    if not wf_event:
        print(f"  ❌ No workflow_created event for {workflow_id}")
        return

    # Check cancelled
    if any(e["event_type"] == "workflow_cancelled" for e in events):
        print(f"  🚫  Workflow {workflow_id} is CANCELLED. Cannot advance.")
        return

    template_name = wf_event.get("metadata", {}).get("template", "")
    try:
        tpl = load_template(template_name)
    except FileNotFoundError:
        print(f"  ❌ Template '{template_name}' not found. Cannot determine next step.")
        return

    steps = tpl.get("steps", [])
    if not steps:
        print(f"  ❌ Template has no steps")
        return

    # Find current step index (last completed or drafted)
    completed_indices = set()
    drafted_indices = set()
    for e in events:
        meta = e.get("metadata", {})
        sid = meta.get("step_id", "")
        step_idx = next(
            (i for i, s in enumerate(steps) if s["step_id"] == sid),
            None,
        )
        if step_idx is not None:
            if e["event_type"] == "workflow_step_completed":
                completed_indices.add(step_idx)
            elif e["event_type"] == "workflow_step_created":
                drafted_indices.add(step_idx)

    skipped_indices = set()
    for e in events:
        if e["event_type"] == "workflow_step_skipped":
            sid = e.get("metadata", {}).get("step_id", "")
            step_idx = next(
                (i for i, s in enumerate(steps) if s["step_id"] == sid),
                None,
            )
            if step_idx is not None:
                skipped_indices.add(step_idx)

    # Find next step to execute
    next_idx = None
    for i, s in enumerate(steps):
        if i in completed_indices or i in skipped_indices:
            continue
        if i not in drafted_indices:
            next_idx = i
            break

    if next_idx is None:
        # Check if all steps are done
        all_done = all(i in completed_indices or i in skipped_indices for i in range(len(steps)))
        if all_done:
            record_ledger_event(
                event_type="workflow_completed",
                source_type="workflow_cli",
                source_id=workflow_id,
                summary=f"Workflow {workflow_id} completed ({len(steps)} steps)",
                metadata={"workflow_id": workflow_id, "total_steps": len(steps)},
            )
            print(f"\n  ✅  Workflow {workflow_id} is COMPLETE!")
            return
        else:
            print(f"  ℹ️  No next step identified. All steps have been drafted or completed.")
            return

    next_step = steps[next_idx]

    # Check dependencies
    deps = next_step.get("depends_on", [])
    for dep in deps:
        dep_step_id = dep["step"]
        dep_idx = next(
            (i for i, s in enumerate(steps) if s["step_id"] == dep_step_id),
            None,
        )
        dep_completed = dep_idx is not None and dep_idx in completed_indices
        dep_skipped = dep_idx is not None and dep_idx in skipped_indices

        if not dep_completed and not dep_skipped:
            record_ledger_event(
                event_type="workflow_blocked",
                source_type="workflow_cli",
                source_id=workflow_id,
                summary=f"Step '{next_step['step_id']}' blocked by '{dep_step_id}' (not completed)",
                metadata={
                    "workflow_id": workflow_id,
                    "step_id": next_step["step_id"],
                    "blocked_reason": f"Dependency '{dep_step_id}' not completed",
                    "blocked_by_step": dep_step_id,
                },
            )
            print(f"\n  🚫  BLOCKED: Step '{next_step['step_id']}' cannot proceed")
            print(f"     Dependency '{dep_step_id}' is not yet completed.")
            print(f"     Use 'resolve' after completing the dependency, or 'skip' to skip it.")
            return

    # ── Asset fallback (3 layers) ──
    context_summary = ""
    dep_step = deps[0] if deps else None
    if dep_step:
        dep_step_id = dep_step["step"]
        consumes_asset_type = dep_step.get("consumes_asset")
        dep_idx = next(
            (i for i, s in enumerate(steps) if s["step_id"] == dep_step_id),
            None,
        )

        # Layer 1: From step metadata (asset_id stored in WO metadata_json)
        dep_completed_events = [
            e for e in events
            if e["event_type"] == "workflow_step_completed"
            and e.get("metadata", {}).get("step_id") == dep_step_id
        ]
        asset_found = False

        for comp_ev in dep_completed_events:
            asset_id = comp_ev.get("metadata", {}).get("asset_id")
            if asset_id:
                context_summary = f"Asset from step '{dep_step_id}': {asset_id}"
                asset_found = True
                break

        # Layer 2: From Asset Registry
        if not asset_found and consumes_asset_type:
            # Try to find the work order for this step
            step_created = next(
                (e for e in events
                 if e["event_type"] == "workflow_step_created"
                 and e.get("metadata", {}).get("step_id") == dep_step_id),
                None,
            )
            if step_created:
                wo_id = step_created.get("metadata", {}).get("draft_id", "")
                asset = query_asset_by_source(
                    source_work_order=wo_id,
                    asset_type=consumes_asset_type,
                )
                if asset:
                    context_summary = f"Asset from Registry: {asset.get('asset_type')} ({asset.get('asset_id')}) — {asset.get('summary', '')}"
                    asset_found = True

        # Layer 3: Fallback to summary
        if not asset_found:
            dep_created = next(
                (e for e in events
                 if e["event_type"] == "workflow_step_created"
                 and e.get("metadata", {}).get("step_id") == dep_step_id),
                None,
            )
            if dep_created:
                context_summary = f"[Fallback] Previous step '{dep_step_id}' completed. Asset details unavailable."
                record_ledger_event(
                    event_type="workflow_blocked",
                    source_type="workflow_cli",
                    source_id=workflow_id,
                    summary=f"Step '{next_step['step_id']}' — asset not found via layers 1-3",
                    metadata={
                        "workflow_id": workflow_id,
                        "step_id": next_step["step_id"],
                        "blocked_reason": "missing_required_asset",
                        "required_asset_type": consumes_asset_type or "unknown",
                    },
                )
                print(f"\n  ⚠️  Missing asset for step '{next_step['step_id']}'")
                print(f"     Required: {consumes_asset_type or 'unknown'}")
                print(f"     Fallback context will be used, but Draft quality may suffer.")
                print(f"     Use 'resolve' to continue, or 'skip' to skip this step.")

    # Check for skip_context from skipped dependencies
    if not context_summary and dep_step:
        dep_step_id = dep_step["step"]
        dep_idx = next(
            (i for i, s in enumerate(steps) if s["step_id"] == dep_step_id),
            None,
        )
        if dep_idx in skipped_indices:
            context_summary = f"[Skip Context] Step '{dep_step_id}' was skipped by Founder. Expected asset '{dep_step.get('consumes_asset', 'unknown')}' is unavailable."

    # ── Generate next step Draft ──
    draft_id = _generate_step_draft(
        wf_id=workflow_id,
        template_name=template_name,
        all_steps=steps,
        step=next_step,
        step_index=next_idx,
        source_asset_summary=context_summary,
    )

    # ── Write events ──
    record_ledger_event(
        event_type="workflow_step_created",
        source_type="workflow_cli",
        source_id=workflow_id,
        summary=f"Step {next_idx + 1} '{next_step['step_id']}' draft generated ({draft_id})",
        metadata={
            "workflow_id": workflow_id,
            "step_id": next_step["step_id"],
            "draft_id": draft_id,
            "step_index": next_idx,
        },
    )

    # Compute unlocked_by
    unlocked_by = []
    for dep in deps:
        unlocked_by.append(dep["step"])
    if unlocked_by:
        record_ledger_event(
            event_type="workflow_step_unlocked",
            source_type="workflow_cli",
            source_id=workflow_id,
            summary=f"Step '{next_step['step_id']}' unlocked by: {', '.join(unlocked_by)}",
            metadata={
                "workflow_id": workflow_id,
                "step_id": next_step["step_id"],
                "unlocked_by_step": unlocked_by,
            },
        )

    print(f"\n  ✅ Step {next_idx + 1}/{len(steps)} ready: {next_step['step_id']}")
    print(f"     Draft: reports/work-order-drafts/{draft_id}.md")
    print(f"     Action: {next_step.get('action', 'TBD')}")
    print(f"     Class:  {next_step.get('action_class', '?')}")
    print()
    print(f"  ℹ️  Founder must review the Draft and approve-create-work-order before execution.")

    # Register step context asset
    if context_summary:
        record_and_register_asset(
            event_type="workflow_step_created",
            source_type="workflow_cli",
            source_id=workflow_id,
            summary=f"Context for step '{next_step['step_id']}': {context_summary[:100]}",
            asset_type="workflow_step_context",
            path=f"reports/work-order-drafts/{draft_id}.md",
        )


# ── Resolve / Skip / Cancel ──────────────────────────────────

def cmd_resolve(workflow_id: str, step_id: str) -> None:
    """Manually resolve a blocked step."""
    record_ledger_event(
        event_type="workflow_block_resolved",
        source_type="workflow_cli",
        source_id=workflow_id,
        summary=f"Block resolved for step {step_id}",
        metadata={
            "workflow_id": workflow_id,
            "step_id": step_id,
            "resolved_by": "founder",
        },
    )
    print(f"\n  ✅ Block resolved for step '{step_id}' in workflow {workflow_id}")
    print(f"  ℹ️  Use 'next' to attempt advancing the workflow.")


def cmd_skip(workflow_id: str, step_id: str) -> None:
    """Skip a workflow step, generating a skip_context asset."""
    # Get template to find the expected asset
    events = _get_events_by_source(workflow_id)
    wf_event = next((e for e in events if e["event_type"] == "workflow_created"), None)
    template_name = wf_event.get("metadata", {}).get("template", "") if wf_event else ""

    expected_asset = "unknown"
    try:
        tpl = load_template(template_name)
        for s in tpl.get("steps", []):
            if s["step_id"] == step_id:
                outputs = s.get("outputs", [])
                if outputs:
                    expected_asset = outputs[0].get("asset_type", "unknown")
                break
    except (FileNotFoundError, yaml.YAMLError):
        pass

    # Generate skip_context asset
    skip_summary = f"Step '{step_id}' was skipped by Founder. The expected '{expected_asset}' asset is unavailable."
    record_and_register_asset(
        event_type="workflow_step_skipped",
        source_type="workflow_cli",
        source_id=workflow_id,
        summary=skip_summary,
        asset_type="workflow_step_context",
        path=f"workflow://{workflow_id}/{step_id}/skipped",
    )

    record_ledger_event(
        event_type="workflow_step_skipped",
        source_type="workflow_cli",
        source_id=workflow_id,
        summary=f"Step '{step_id}' skipped by Founder",
        metadata={
            "workflow_id": workflow_id,
            "step_id": step_id,
            "skip_reason": "founder_command",
            "expected_asset_type": expected_asset,
        },
    )

    print(f"\n  ⏭️  Step '{step_id}' skipped in workflow {workflow_id}")
    print(f"     Expected asset '{expected_asset}' replaced with skip_context.")
    print(f"  ℹ️  Use 'next' to attempt advancing to the next step.")


def cmd_cancel(workflow_id: str) -> None:
    """Cancel an entire workflow."""
    record_ledger_event(
        event_type="workflow_cancelled",
        source_type="workflow_cli",
        source_id=workflow_id,
        summary=f"Workflow {workflow_id} cancelled by Founder",
        metadata={
            "workflow_id": workflow_id,
            "cancelled_by": "founder",
            "reason": "founder_command",
        },
    )
    print(f"\n  🚫 Workflow {workflow_id} CANCELLED")
    print(f"     All incomplete steps are marked as cancelled.")
    print(f"     Run 'status' to confirm.")


# ── CLI ───────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="v0.30 — Workflow Runner CLI: orchestrate multi-step Work Orders",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # create
    create_p = sub.add_parser("create", help="Create a new workflow from a template")
    create_p.add_argument("--template", "-t", required=True, help="Template name")
    create_p.add_argument("--context", "-c", default="", help="Founder context / description")

    # status
    status_p = sub.add_parser("status", help="Show workflow status")
    status_p.add_argument("workflow_id", help="Workflow ID (e.g. WF-20260517-001)")

    # next
    next_p = sub.add_parser("next", help="Advance workflow to next step")
    next_p.add_argument("workflow_id", help="Workflow ID")

    # resolve
    resolve_p = sub.add_parser("resolve", help="Resolve a blocked step")
    resolve_p.add_argument("workflow_id", help="Workflow ID")
    resolve_p.add_argument("step_id", help="Step ID to resolve")

    # skip
    skip_p = sub.add_parser("skip", help="Skip a workflow step")
    skip_p.add_argument("workflow_id", help="Workflow ID")
    skip_p.add_argument("step_id", help="Step ID to skip")

    # cancel
    cancel_p = sub.add_parser("cancel", help="Cancel the entire workflow")
    cancel_p.add_argument("workflow_id", help="Workflow ID")

    # templates
    list_p = sub.add_parser("templates", help="List available templates")

    args = parser.parse_args()

    if args.command == "create":
        cmd_create(args.template, args.context)
    elif args.command == "status":
        cmd_status(args.workflow_id)
    elif args.command == "next":
        cmd_next(args.workflow_id)
    elif args.command == "resolve":
        cmd_resolve(args.workflow_id, args.step_id)
    elif args.command == "skip":
        cmd_skip(args.workflow_id, args.step_id)
    elif args.command == "cancel":
        cmd_cancel(args.workflow_id)
    elif args.command == "templates":
        templates = list_templates()
        if templates:
            print(f"\n  📋 Available Templates:")
            for t in templates:
                print(f"     • {t}")
        else:
            print(f"\n  ℹ️  No templates found.")
        print()


if __name__ == "__main__":
    main()
