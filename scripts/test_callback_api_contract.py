#!/usr/bin/env python3
"""
v0.14.2 — Callback API Contract Test

Tests the HTTP callback API endpoint independently of the full E2E workflow.

Tests:
  1. Create WO via HTTP API, route it, send callback via HTTP
  2. Idempotent callback (same status twice)
  3. Force overwrite callback
  4. Invalid API key rejection
  5. Invalid status rejection
  6. Missing required fields

This test is SEPARATE from the main E2E suite (e2e_openclaw_agent_executor.py)
because it uses HTTP API calls for WO lifecycle, while the main E2E suite
uses pure Python API calls to avoid mixed-mode issues.
"""
import json
import os
import sys
import uuid
import urllib.request

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
CALLBACK_API_KEY = os.environ.get("OPENCLAW_CALLBACK_API_KEY", "oc-test-key-change-me")

PASS = 0
FAIL = 0


def test(name: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} — {detail}")


def step_header(s: str):
    print(f"\n{'='*60}")
    print(f" {s}")
    print(f"{'='*60}")


def api(method: str, path: str, data: dict = None, api_key: str = None) -> dict:
    """Make an HTTP API call to the backend."""
    url = f"{BACKEND_URL}{path}"
    headers = {"Content-Type": "application/json"}

    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    for k, v in headers.items():
        req.add_header(k, v)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return {
                "status": resp.status,
                "body": json.loads(resp.read().decode()),
            }
    except urllib.error.HTTPError as e:
        err_body = e.read().decode() if e.read() else "{}"
        try:
            parsed = json.loads(err_body)
        except json.JSONDecodeError:
            parsed = {"detail": err_body[:200]}
        return {
            "status": e.code,
            "body": parsed,
        }
    except Exception as e:
        return {"status": 0, "body": {"detail": str(e)}}


def create_work_order() -> tuple[str, dict]:
    """Create a work order via HTTP API. Returns (wo_id, wo_dict)."""
    body = {
        "goal_session_id": "GS-CALLBACK-TEST",
        "product_line_id": "ai-company-os",
        "skill_id": "openclaw_external_agent",
        "task_type": "read_context_and_write_summary",
        "execution_mode": "openclaw_bridge_v2",
        "input_context": "Callback API contract test.",
        "expected_output": "callback-test-output.md",
        "risk_level": "low",
    }
    result = api("POST", "/api/v1/work-orders", data=body)
    wo = result["body"]
    return wo.get("work_order_id", ""), wo


def route_work_order(wo_id: str) -> dict:
    """Route a work order via HTTP API."""
    return api("POST", f"/api/v1/work-orders/{wo_id}/route")


def execute_work_order(wo_id: str) -> dict:
    """Execute a WO via HTTP API to set status = in_progress."""
    return api("POST", f"/api/v1/work-orders/{wo_id}/execute")


def send_callback(wo_id: str, body: dict, api_key: str = None) -> dict:
    """Send a callback via HTTP API.

    API key goes in the body (matching the backend's convention),
    not as a header.
    """
    payload = dict(body)  # copy
    payload["api_key"] = api_key or CALLBACK_API_KEY
    return api("POST", f"/api/v1/work-orders/{wo_id}/openclaw-callback", data=payload)


# ---- Tests ----


def test_callback_happy_path():
    """Full callback flow: create WO -> route -> execute -> callback -> verify."""
    step_header("1. Happy path: create WO -> route -> callback -> completed")

    wo_id, wo = create_work_order()
    test("WO created", bool(wo_id), wo_id)
    test("WO status = created", wo.get("status") == "created", str(wo.get("status")))

    route_result = route_work_order(wo_id)
    test("WO routed", route_result["status"] == 200, str(route_result["status"]))
    test("WO status = routed", route_result["body"].get("status") == "routed",
         str(route_result["body"].get("status")))

    # Execute WO to set status = in_progress (callback requires in_progress or dispatched)
    exec_result = api("POST", f"/api/v1/work-orders/{wo_id}/execute")
    test("WO executing", exec_result["status"] == 200, str(exec_result["status"]))
    test("WO status = in_progress", exec_result["body"].get("status") == "in_progress",
         str(exec_result["body"].get("status")))

    # Send callback (simulating a Worker completing the task)
    callback_body = {
        "status": "completed",
        "result_summary": f"Callback contract test completed for {wo_id}",
        "output_path": f"/tmp/artifacts/{wo_id}/output.md",
        "artifacts": [
            {"name": "output.md", "path": f"/tmp/artifacts/{wo_id}/output.md", "type": "markdown"}
        ],
        "confidence": 0.95,
    }
    cb_result = send_callback(wo_id, callback_body)
    cb_body = cb_result["body"]
    test("Callback accepted", cb_result["status"] == 200, str(cb_result["status"]))
    # Response format: {"status": "accepted", "work_order": {...}, "artifacts": [...]}
    wo_result = cb_body.get("work_order", {})
    test("Callback accepted status",
         cb_body.get("status") == "accepted",
         str(cb_body.get("status")))
    test("WO status = completed via callback",
         wo_result.get("status") == "completed",
         str(wo_result.get("status")))
    test("result_summary set via callback",
         bool(wo_result.get("result_summary")),
         wo_result.get("result_summary", "")[:50])
    test("artifacts stored",
         len(cb_body.get("artifacts", [])) > 0,
         str(len(cb_body.get("artifacts", []))))

    return wo_id


def test_idempotent_callback():
    """Same status ('completed') twice should succeed."""
    step_header("2. Idempotent callback: same status twice")

    wo_id, _ = create_work_order()
    route_work_order(wo_id)
    execute_work_order(wo_id)

    # First callback
    cb1 = send_callback(wo_id, {"status": "completed", "result_summary": "first complete"})
    test("First callback accepted", cb1["status"] == 200)

    # Second callback with same status
    cb2 = send_callback(wo_id, {"status": "completed", "result_summary": "second complete"})
    cb2_wo = cb2["body"].get("work_order", {}) if cb2["body"].get("work_order") else cb2["body"]
    test("Idempotent callback accepted", cb2["status"] == 200,
         str(cb2["status"]))
    test("Status still = completed", cb2_wo.get("status") == "completed",
         str(cb2_wo.get("status")))

    return wo_id


def test_force_overwrite():
    """Force overwrite from completed to completed with new data."""
    step_header("3. Force overwrite: completed -> completed with new data")

    wo_id, _ = create_work_order()
    route_work_order(wo_id)
    execute_work_order(wo_id)

    # First callback
    send_callback(wo_id, {"status": "completed", "result_summary": "original"})

    # Force overwrite
    cb2 = send_callback(wo_id, {
        "status": "completed",
        "result_summary": "overwritten by force",
        "force": True,
    })
    cb2_wo = cb2["body"].get("work_order", {}) if cb2["body"].get("work_order") else cb2["body"]
    test("Force overwrite accepted", cb2["status"] == 200, str(cb2["status"]))
    test("Status = completed", cb2_wo.get("status") == "completed")
    test("Result updated to overwritten",
         "overwritten" in cb2_wo.get("result_summary", ""),
         cb2_wo.get("result_summary", ""))

    return wo_id


def test_invalid_api_key():
    """Request with invalid API key should be rejected."""
    step_header("4. Invalid API key rejection")

    wo_id, _ = create_work_order()
    route_work_order(wo_id)
    execute_work_order(wo_id)

    result = send_callback(wo_id, {"status": "completed"}, api_key="wrong-key")
    test("Invalid API key rejected", result["status"] in (401, 403),
         f"status={result['status']}, body={result['body']}")

    return wo_id


def test_invalid_status():
    """Callback with invalid status should be rejected."""
    step_header("5. Invalid status rejection")

    wo_id, _ = create_work_order()
    route_work_order(wo_id)

    result = send_callback(wo_id, {"status": "invalid_status"})
    test("Invalid status rejected", result["status"] in (400, 422),
         f"status={result['status']}, body={str(result['body'])[:100]}")

    return wo_id


def test_missing_required_fields():
    """Callback without required fields should be rejected."""
    step_header("6. Missing required fields")

    wo_id, _ = create_work_order()
    route_work_order(wo_id)

    result = send_callback(wo_id, {})
    test("Missing status rejected", result["status"] in (400, 422),
         f"status={result['status']}, body={str(result['body'])[:100]}")

    return wo_id


def run_all():
    """Run all callback API contract tests."""
    print("=" * 70)
    print(" v0.14.2 -- Callback API Contract Test")
    print("=" * 70)

    # Check backend is running first
    health = api("GET", "/api/v1/health")
    test("Backend is running", health["status"] == 200, str(health))

    if health["status"] != 200:
        print("\n ❌ Backend not available. Start with:")
        print("    cd backend && python3 -m uvicorn app.main:app --port 8001")
        global FAIL
        FAIL += 1
        return False

    test_callback_happy_path()
    test_idempotent_callback()
    test_force_overwrite()
    test_invalid_api_key()
    test_invalid_status()
    test_missing_required_fields()

    total = PASS + FAIL
    print(f"\n{'='*70}")
    print(f" Results: {PASS}/{total} passed, {FAIL}/{total} failed")
    if FAIL == 0:
        print(" ✅ ALL CALLBACK API CONTRACT TESTS PASSED")
        print(f"\n  Callback API endpoints verified:")
        print(f"  ✅ Happy path: WO -> callback -> completed")
        print(f"  ✅ Idempotency: same status twice")
        print(f"  ✅ Force overwrite")
        print(f"  ✅ Invalid API key rejection")
        print(f"  ✅ Invalid status rejection")
        print(f"  ✅ Missing required fields rejection")
    else:
        print(" ❌ SOME TESTS FAILED")
    print(f"{'='*70}")
    return FAIL == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
