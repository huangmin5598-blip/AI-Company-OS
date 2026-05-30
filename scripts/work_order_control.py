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
import sys
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE_URL = "http://localhost:8001/api/v1"


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


TERMINAL_STATUSES = {"completed", "failed", "cancelled", "needs_review"}


def cmd_wait_result(wo_id: str, timeout: int = 180):
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
    wr.add_argument("--verbose", "-v", action="store_true", help="Show all poll results")

    args = parser.parse_args()

    if args.command == "approve-dispatch":
        cmd_approve_dispatch(args.wo_id)
    elif args.command == "wait-result":
        cmd_wait_result(args.wo_id, timeout=args.timeout)


if __name__ == "__main__":
    main()
