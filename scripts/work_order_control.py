#!/usr/bin/env python3
"""
v0.21 — Work Order Control: approve-dispatch

Founder approval gate for created Work Orders.
Calls existing API endpoints — does NOT reimplement routing/execution.

Usage:
    python3 scripts/work_order_control.py approve-dispatch <WO_ID>

Flow:
    1. Read WO → validate status=created & approval_required=true
    2. Write approved_for_dispatch_at + approval_id
    3. POST /route (fills skill_id, runtime, risk, etc.)
    4. POST /execute (transitions to in_progress)
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


def main():
    parser = argparse.ArgumentParser(
        description="v0.21 — Work Order Control (approve-dispatch gate)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # approve-dispatch
    ad = subparsers.add_parser("approve-dispatch", help="Approve and dispatch a Work Order")
    ad.add_argument("wo_id", help="Work Order ID (e.g. WO-BA399DE7)")
    ad.add_argument("--verbose", "-v", action="store_true", help="Show full WO detail on errors")

    args = parser.parse_args()

    if args.command == "approve-dispatch":
        cmd_approve_dispatch(args.wo_id)


if __name__ == "__main__":
    main()
