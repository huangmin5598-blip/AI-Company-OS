#!/usr/bin/env python3
""""
v0.22 — Work Order Control: approve-dispatch, wait-result

Founder approval gate for created Work Orders.
Calls existing API endpoints — does NOT reimplement routing/execution.

Usage:
    python3 scripts/work_order_control.py approve-dispatch <WO_ID>
    python3 scripts/work_order_control.py wait-result <WO_ID> [--timeout 180]

Flows:
    approve-dispatch:
        1. Read WO → validate status=created & approval_required=true
        2. Write approved_for_dispatch_at + approval_id
        3. POST /route (fills skill_id, runtime, risk, etc.)
        4. POST /execute (transitions to in_progress via WorkOrderExecutor)

    wait-result:
        1. Poll GET /work-orders/{id} every 5s
        2. Until status ∈ {completed, failed, cancelled, needs_review}
        3. Print result_summary, artifact_path, final status
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE_URL = "http://localhost:8001/api/v1"

# Module-level script dir for backend path resolution
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))

# ── Backend DB helper (optional, for Run Ledger) ──────────────────────

def _record_os_event(event_type, source_type="", source_id="", work_order_id="",
                     decision_id="", draft_id="", summary="", metadata=None):
    """Record an OS event + register asset if applicable.

    Graceful: if backend is not set up or DB unavailable, prints [SKIP].
    """
    try:
        backend_dir = os.path.join(_PROJECT_ROOT, "backend")
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        _old_cwd = os.getcwd()
        os.chdir(backend_dir)
        from app.services.run_ledger_service import record_and_register, record_event
        if event_type in ("result_synced",):
            r = record_and_register(
                event_type=event_type, asset_type="execution_result",
                source_type=source_type, source_id=source_id,
                work_order_id=work_order_id, decision_id=decision_id,
                draft_id=draft_id, summary=summary,
                metadata=metadata,
            )
            if r["event_recorded"]:
                print(f"  📋 Run Ledger: {event_type} recorded")
            if r["asset_id"]:
                print(f"  📦 Asset Registry: execution_result asset {r['asset_id']}")
        else:
            r = record_event(
                event_type=event_type, source_type=source_type,
                source_id=source_id, work_order_id=work_order_id,
                decision_id=decision_id, draft_id=draft_id,
                summary=summary, metadata=metadata,
            )
            if r:
                print(f"  📋 Run Ledger: {event_type} recorded")
        os.chdir(_old_cwd)
    except Exception as e:
        os.chdir(_old_cwd)
        print(f"  [SKIP] Run Ledger write skipped ({e})")


def _api_get(path: str) -> dict:
    url = f"{BASE_URL}{path}"
    req = Request(url, method="GET")
    with urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def _api_post(path: str, data: dict | None = None) -> dict:
    url = f"{BASE_URL}{path}"
    body = json.dumps(data or {}).encode()
    req = Request(url, method="POST", data=body,
                  headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def _api_patch(path: str, data: dict) -> dict:
    import json as _json
    url = f"{BASE_URL}{path}"
    body = _json.dumps(data).encode()
    req = Request(url, method="PATCH", data=body,
                  headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=15) as resp:
        return _json.loads(resp.read().decode())


def _now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _fmt(d: dict) -> str:
    """Pretty-print a dict as key: value pairs."""
    return "\n".join(f"  {k}: {v}" for k, v in d.items() if v)


def cmd_approve_dispatch(wo_id: str):
    # ── 0. Policy check (advisory) ──
    try:
        from scripts.policy_resolver import check_and_record
        policy = check_and_record(
            actor_id="founder-console-api",
            action="approve_dispatch",
            source_id=wo_id,
            summary=f"Policy check for approve-dispatch {wo_id}",
            record=True,
        )
        if policy.get("requires_founder_approval"):
            print(f"  🔒 Founder approval required — proceeding (advisory mode)")
        if policy.get("verdict") in ("BLOCKED",):
            print(f"  🚫 Policy blocked: {policy.get('reason', '')}")
            sys.exit(1)
    except ImportError:
        pass

    # ── 1. Read WO ──
    print(f"[v0.21] Reading Work Order: {wo_id}")
    try:
        wo = _api_get(f"/work-orders/{wo_id}")
    except HTTPError as e:
        if e.code == 404:
            print(f"[FAIL] WO '{wo_id}' not found")
            sys.exit(1)
        raise

    # ── 2. Validate ──
    current_status = wo.get("status", "")
    if current_status != "created":
        print(f"[FAIL] WO status is '{current_status}', expected 'created'")
        print(f"  → Already processed or in wrong state for approval")
        sys.exit(1)

    if not wo.get("approval_required", False):
        print(f"[FAIL] WO does not require approval (approval_required=false)")
        print(f"  → No approval gate needed; use route+execute directly")
        sys.exit(1)

    if wo.get("approved_for_dispatch_at"):
        print(f"[FAIL] WO already approved at {wo['approved_for_dispatch_at']}")
        print(f"  → approve-dispatch already completed")
        sys.exit(1)

    print(f"  task_type:     {wo.get('task_type', '')}")
    print(f"  risk_level:    {wo.get('risk_level', '')}")
    print(f"  approval_req:  {wo.get('approval_required', False)}")
    print(f"  input_context: {wo.get('input_context', '')[:80]}...")
    print()

    # ── 3. Write approval timestamp + approval_id ──
    now = _now_str()
    approval_id = f"FOUNDER-{int(time.time())}"
    print(f"[v0.21] Writing approval: {now}, approval_id={approval_id}")
    try:
        updated = _api_patch(f"/work-orders/{wo_id}", {
            "approved_for_dispatch_at": now,
            "approval_id": approval_id,
        })
        print(f"  approved_for_dispatch_at: {updated.get('approved_for_dispatch_at')}")
        print(f"  approval_id:              {updated.get('approval_id')}")
    except HTTPError as e:
        print(f"[FAIL] Could not write approval: HTTP {e.code}")
        sys.exit(1)
    print()

    # ── 4. Route ──
    print(f"[v0.21] Routing WO: POST /work-orders/{wo_id}/route")
    try:
        routed = _api_post(f"/work-orders/{wo_id}/route")
        route_status = routed.get("status", "")
        if route_status == "needs_review":
            print(f"[FAIL] Routing failed: needs_review")
            print(f"  reason: {routed.get('reason', 'unknown')}")
            print(f"  → task_type '{wo.get('task_type', '')}' has no matching skill in registry")
            sys.exit(1)
        print(f"  skill_id:      {routed.get('skill_id', '')}")
        print(f"  runtime_id:    {routed.get('runtime_id', '')}")
        print(f"  execution_mode:{routed.get('execution_mode', '')}")
        print(f"  risk_level:    {routed.get('risk_level', '')}")
        print(f"  assigned_agent:{routed.get('assigned_agent', '')}")
    except HTTPError as e:
        body = e.read().decode() if hasattr(e, 'read') else ""
        print(f"[FAIL] Route failed: HTTP {e.code} {body[:200]}")
        sys.exit(1)
    print()

    # ── 5. Execute (with approval already set) ──
    print(f"[v0.21] Executing WO: POST /work-orders/{wo_id}/execute")
    try:
        executed = _api_post(f"/work-orders/{wo_id}/execute")
        final_status = executed.get("status", "")
        print(f"  status:        {final_status}")
        print(f"  attempt_count: {executed.get('attempt_count', 0)}")
    except HTTPError as e:
        body = e.read().decode() if hasattr(e, 'read') else ""
        print(f"[FAIL] Execute failed: HTTP {e.code} {body[:300]}")
        print(f"  → Approval was written, route succeeded, but execution blocked")
        sys.exit(1)

    # ── 6. Summary ──
    print()
    print("=" * 50)
    print(f"✅ APPROVE-DISPATCH COMPLETE")
    print("=" * 50)
    print(f"  WO ID:             {wo_id}")
    print(f"  Approved at:       {now}")
    print(f"  Approval ID:       {approval_id}")
    print(f"  Status:            created → routed → {final_status}")
    print(f"  Skill:             {routed.get('skill_id', '')}")
    print(f"  Agent:             {routed.get('assigned_agent', '')}")
    print(f"  Runtime:           {routed.get('runtime_id', '')}")
    print(f"  Execution Mode:    {routed.get('execution_mode', '')}")
    print("=" * 50)

    # ── Record OS events ──
    decision_id = _extract_source_field(wo, "source_decision")
    draft_id_raw = _extract_source_field(wo, "source_draft")
    _record_os_event("approved_for_dispatch", source_type="api", source_id=wo_id,
                     work_order_id=wo_id, decision_id=decision_id,
                     summary=f"WO {wo_id} approved (approval_id={approval_id})")
    _record_os_event("work_order_routed", source_type="api", source_id=wo_id,
                     work_order_id=wo_id,
                     summary=f"WO {wo_id} routed to {routed.get('skill_id', '?')}")
    _record_os_event("work_order_executed", source_type="api", source_id=wo_id,
                     work_order_id=wo_id,
                     summary=f"WO {wo_id} executed (mode={routed.get('execution_mode', '?')})")


TERMINAL_STATUSES = {"completed", "failed", "cancelled", "needs_review"}


def _extract_source_field(wo: dict, field: str) -> str:
    """Extract a source metadata field from a Work Order's routing_log_json.

    Supports both v0.20 format (flat keys) and v0.22 format (nested under _source).
    """
    rlj = wo.get("routing_log_json", "")
    if not rlj:
        return ""

    try:
        import json as _json
        src = _json.loads(rlj) if isinstance(rlj, str) else rlj
    except (_json.JSONDecodeError, TypeError):
        return ""

    if not isinstance(src, dict):
        return ""

    # v0.22+: nested under _source
    if "_source" in src and isinstance(src["_source"], dict):
        val = src["_source"].get(field, "")
        if val:
            return val

    # v0.20: flat keys
    val = src.get(field, "")
    return val if isinstance(val, str) else ""


def _sync_source_draft(wo_id: str, wo: dict):
    """Append execution result to the source Work Order Draft file.

    Idempotent: skips if draft already has '## Execution Result' section.
    Silent: prints warning if source_draft not found, but does not fail.
    """
    import os as _os

    # Parse source metadata from routing_log_json
    source_draft = _extract_source_field(wo, "source_draft")
    if not source_draft:
        print(f"[SKIP] No source_draft in work order metadata")
        return

    # Resolve path relative to project root
    project_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    draft_path = _os.path.join(project_root, source_draft)

    if not _os.path.exists(draft_path):
        print(f"[SKIP] Source draft not found: {source_draft}")
        return

    # Read draft, check for existing Execution Result section (idempotent)
    with open(draft_path, "r", encoding="utf-8") as f:
        draft_text = f.read()

    if "## Execution Result" in draft_text:
        print(f"[SKIP] Draft already has Execution Result — not overwriting")
        return

    # Append execution result section
    result_text = wo.get("result_summary", "")
    completed_at = wo.get("completed_at", "")
    output_path = wo.get("output_path", "")
    artifacts = wo.get("artifacts_json", "")
    executor = wo.get("execution_mode", "")
    agent = wo.get("assigned_agent", "")

    execution_section = f"""
---

## Execution Result

- **work_order_id:** {wo_id}
- **status:** {wo.get('status', '')}
- **completed_at:** {completed_at}
- **result_summary:** {result_text}
- **artifact_path:** {output_path}
- **artifacts:** {artifacts}
- **executor:** {executor}
- **agent:** {agent}

_draft_status: completed_
"""

    with open(draft_path, "a", encoding="utf-8") as f:
        f.write(execution_section)

    print(f"  ✓ Source draft updated: {source_draft}")
    print(f"    → status: completed")

    # Also update INDEX.md
    _update_draft_index(project_root, source_draft, wo_id, wo)


def _update_draft_index(project_root: str, source_draft: str, wo_id: str, wo: dict):
    """Update the work-order-drafts INDEX.md to reflect completed status."""
    import os as _os

    index_path = _os.path.join(project_root, "reports", "work-order-drafts", "INDEX.md")
    if not _os.path.exists(index_path):
        print(f"  [SKIP] INDEX.md not found")
        return

    with open(index_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    draft_filename = _os.path.basename(source_draft)
    result_summary = (wo.get("result_summary", "") or "")[:60]
    completed_at = wo.get("completed_at", "") or ""

    new_lines = []
    updated = False
    for line in lines:
        if draft_filename in line and "|" in line:
            parts = line.split("|")
            if len(parts) >= 7:
                # Old format: | Draft | Brief | Decision | Title | created | WO-ID |
                # New format: | Draft | Brief | Decision | Title | completed | WO-ID | Result | Completed At |
                title_part = parts[3].strip() if len(parts) > 3 else ""
                wo_id_part = parts[5].strip() if len(parts) > 5 else wo_id

                new_line = f"| {parts[1].strip()} | {parts[2].strip()} | {title_part} | completed | {wo_id_part} | {result_summary} | {completed_at} |\n"
                new_lines.append(new_line)
                updated = True
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    if updated:
        # Update header to include new columns
        header_updated = False
        final_lines = []
        for line in new_lines:
            if line.startswith("|") and "Draft" in line and "Source Brief" in line and not header_updated:
                final_lines.append("| Draft | Source Brief | Title | Status | Work Order ID | Result | Completed At |\n")
                final_lines.append("|-------|-------------|-------|--------|---------------|--------|-------------|\n")
                header_updated = True
            else:
                final_lines.append(line)

        with open(index_path, "w", encoding="utf-8") as f:
            f.writelines(final_lines)
        print(f"  ✓ INDEX.md updated — {draft_filename} → completed")
    else:
        print(f"  [SKIP] Could not update INDEX.md — draft {draft_filename} not found in table")


def _sync_decision_log(wo_id: str, wo: dict):
    """Append an Execution Completed entry to DECISION-LOG.md.

    Idempotent: skips if WO ID already appears in the log.
    Creates DECISION-LOG.md if it doesn't exist.
    """
    import os as _os

    project_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    decision_log_path = _os.path.join(project_root, "reports", "ceo-brief-reviews", "DECISION-LOG.md")

    # Parse source metadata
    source_decision = _extract_source_field(wo, "source_decision")
    source_brief = _extract_source_field(wo, "source_brief")

    result_summary = wo.get("result_summary", "") or ""
    completed_at = wo.get("completed_at", "") or ""

    # Read or create
    if _os.path.exists(decision_log_path):
        with open(decision_log_path, "r", encoding="utf-8") as f:
            log_text = f.read()
    else:
        log_text = ""

    # Idempotency: check if WO ID already logged
    if f"WO-{wo_id[3:]}" in log_text or wo_id in log_text:
        print(f"[SKIP] Decision Log already contains {wo_id}")
        return

    # Append a new row
    from datetime import datetime as _dt
    now_str = _dt.now().strftime("%Y-%m-%d %H:%M:%S")

    note = f"WO {wo_id} completed: {result_summary[:60]}"
    entry = f"| {now_str[:10]} | {wo_id} | {source_brief or '—'} | {result_summary[:80]} | Execution Completed | {note} | {now_str} |\n"

    if log_text.strip():
        # Append to existing table
        # Find the last table row and insert after it
        if log_text.rstrip().endswith("|"):
            append_text = "\n" + entry
        else:
            append_text = "\n" + entry
    else:
        # Create new file
        append_text = f"""# CEO Brief — Decision Log

_Auto-generated. Append-only._
_Created: {now_str}_

| Date | Source | Summary | Decision | Notes | Completed At | Logged At |
|------|--------|---------|----------|-------|-------------|-----------|
{entry}"""

    with open(decision_log_path, "a", encoding="utf-8") as f:
        f.write(append_text)

    print(f"  ✓ Decision Log updated — {wo_id} → Execution Completed")


def cmd_wait_result(wo_id: str, timeout: int = 180, sync_source: bool = False):
    """Poll a Work Order until it reaches a terminal status."""
    import time as _time

    deadline = _time.time() + timeout
    interval = 5
    poll_count = 0

    print(f"[v0.22] Waiting for WO {wo_id} to complete (timeout={timeout}s)...")
    print(f"  Polling every {interval}s...")
    print()

    while _time.time() < deadline:
        poll_count += 1
        try:
            wo = _api_get(f"/work-orders/{wo_id}")
        except HTTPError as e:
            if e.code == 404:
                print(f"[FAIL] WO '{wo_id}' not found during polling")
                sys.exit(1)
            print(f"[WARN] Poll error HTTP {e.code} — retrying...")
            _time.sleep(interval)
            continue

        status = wo.get("status", "")
        result_summary = wo.get("result_summary", "")

        # Print progress every 5 polls
        if poll_count % 5 == 1 or status in TERMINAL_STATUSES:
            print(f"  [{poll_count}] status={status} elapsed={int(_time.time() - (deadline - timeout))}s"
                  f"{' summary=' + result_summary[:60] if result_summary else ''}")

        if status in TERMINAL_STATUSES:
            print()
            print("=" * 50)
            print(f"🏁 WO {wo_id} — {status.upper()}")
            print("=" * 50)
            print(f"  Status:          {status}")
            print(f"  Result summary:  {result_summary}")
            print(f"  Output path:     {wo.get('output_path', '')}")
            print(f"  Completed at:    {wo.get('completed_at', '')}")
            print(f"  Artifacts:       {wo.get('artifacts_json', '')[:100]}")
            if wo.get("error"):
                print(f"  Error:           {wo['error']}")
            print(f"  Polls:           {poll_count}")
            print("=" * 50)

            # ── Sync source artifacts if requested ──
            if sync_source and status == "completed":
                _sync_source_draft(wo_id, wo)
                _sync_decision_log(wo_id, wo)
                # ── Record result_synced event ──
                _record_os_event(
                    "result_synced", source_type="api", source_id=wo_id,
                    work_order_id=wo_id,
                    summary=f"WO {wo_id} result synced to source draft + decision log",
                    metadata={
                        "status": status,
                        "result_summary": wo.get("result_summary", ""),
                        "output_path": wo.get("output_path", ""),
                    },
                )
            elif sync_source and status != "completed":
                print(f"[SKIP] --sync-source only applies to completed WO (current: {status})")

            return

        _time.sleep(interval)

    # Timeout
    print(f"[FAIL] Timeout after {timeout}s — WO {wo_id} still in status '{status}'")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="v0.22 — Work Order Control (approve-dispatch, wait-result)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # approve-dispatch
    ad = subparsers.add_parser("approve-dispatch", help="Approve and dispatch a Work Order")
    ad.add_argument("wo_id", help="Work Order ID (e.g. WO-BA399DE7)")
    ad.add_argument("--verbose", "-v", action="store_true", help="Show full WO detail on errors")

    # wait-result
    wr = subparsers.add_parser("wait-result", help="Wait for a Work Order to complete")
    wr.add_argument("wo_id", help="Work Order ID (e.g. WO-BA399DE7)")
    wr.add_argument("--timeout", type=int, default=180, help="Max seconds to wait (default: 180)")
    wr.add_argument("--sync-source", action="store_true", help="Backfill execution result to source draft + decision log")
    wr.add_argument("--verbose", "-v", action="store_true", help="Show all poll results")

    args = parser.parse_args()

    if args.command == "approve-dispatch":
        cmd_approve_dispatch(args.wo_id)
    elif args.command == "wait-result":
        cmd_wait_result(args.wo_id, timeout=args.timeout, sync_source=args.sync_source)


if __name__ == "__main__":
    main()
