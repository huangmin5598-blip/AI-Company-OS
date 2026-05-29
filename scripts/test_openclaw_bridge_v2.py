#!/usr/bin/env python3
"""
v0.13 OpenClaw Bridge v2 — Integration Test Suite

Tests the full lifecycle:
  Scenario A: External Interaction Draft (customer service)
  Scenario B: Research Task
  Timeout behavior
  Malformed result.json
  Idempotent callback
  Polling lifecycle
"""
import json
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.openclaw_bridge import OpenClawBridge
from app.services.openclaw_callback import (
    validate_api_key,
    validate_callback_body,
    check_idempotent,
    apply_callback_to_work_order,
)
from app.database import get_sync_session, init_db, upgrade_schema_v013
from app.models.work_order import WorkOrder
from app.services.work_order_executor import EXECUTION_HANDLERS

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


def setup_module():
    """Ensure DB schema is up to date and clean up leftover task files."""
    openclaw_dir = os.path.expanduser("~/.ai-company-os/openclaw")
    for subdir in ["inbox", "working"]:
        d = os.path.join(openclaw_dir, subdir)
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith(".task.json"):
                    os.remove(os.path.join(d, f))
    init_db()
    upgrade_schema_v013()


def test_bridge_creation():
    """Test basic bridge creation and directory readiness."""
    print("\n--- Test: Bridge Creation ---")
    bridge = OpenClawBridge()
    test("Bridge is ready", bridge.is_ready)
    test("INBOX_DIR exists", os.path.isdir(os.path.expanduser("~/.ai-company-os/openclaw/inbox")))
    test("WORKING_DIR exists", os.path.isdir(os.path.expanduser("~/.ai-company-os/openclaw/working")))
    return bridge


def test_create_task_card(bridge: OpenClawBridge):
    """Test creating a task card with full schema."""
    print("\n--- Test: Create Task Card ---")
    wo = {
        "work_order_id": "WO-INTEGRATION-TEST-A",
        "goal_session_id": "GS-TEST",
        "product_line_id": "ai-seller-finance",
        "task_type": "customer_response",
        "input_context": "用户问：利润报告支持哪个站点的数据？",
        "expected_output": "response-draft.md",
        "risk_level": "low",
        "allowed_actions": ["read_faq", "write_response"],
        "forbidden_actions": ["send_email", "deploy", "delete_file", "modify_code"],
        "allowed_tools": ["faq_reader"],
        "timeout_seconds": 60,
        "requires_human_review": True,
        "execution_mode": "openclaw_bridge_v2",
    }

    result = bridge.create_task_card(wo)
    test("Card created with status 'dispatched_to_openclaw'",
         result["status"] == "dispatched_to_openclaw", str(result.get("status")))
    test("Card has card_id", bool(result.get("card_id")))
    test("Card has card_path", bool(result.get("card_path")))
    test("Card written to inbox",
         os.path.exists(result.get("card_path", "")),
         result.get("card_path", ""))

    # Verify the card content
    card_path = result["card_path"]
    with open(card_path, encoding="utf-8") as f:
        card = json.load(f)
    test("Card contains work_order_id", card.get("work_order_id") == "WO-INTEGRATION-TEST-A")
    test("Card contains forbidden_actions", "forbidden_actions" in card)
    test("Card contains allowed_actions", "allowed_actions" in card)
    test("Card contains report_back_path", bool(card.get("report_back_path")))
    test("Card contains timeout_seconds", card.get("timeout_seconds") == 60)
    test("Card contains requires_human_review", card.get("requires_human_review") is True)

    return result


def test_claim_lifecycle(bridge: OpenClawBridge):
    """Test simulate_claim and task state detection."""
    print("\n--- Test: Claim Lifecycle ---")
    wo_id = "WO-CLAIM-LIFECYCLE"
    bridge.create_task_card({"work_order_id": wo_id, "expected_output": "test"})

    state_before = bridge.get_task_state(wo_id)
    test("State is 'dispatched' before claim",
         state_before == "dispatched", state_before)

    claim_result = bridge.simulate_claim(wo_id)
    test("Claim returns 'claimed_by_openclaw'",
         claim_result["status"] == "claimed_by_openclaw", str(claim_result.get("status")))

    state_after = bridge.get_task_state(wo_id)
    test("State is 'claimed' after claim",
         state_after == "claimed", state_after)

    # Verify card now in working directory
    working_path = bridge.get_task_card_path(wo_id)
    test("Task card path now in working directory",
         "working" in (working_path or ""), str(working_path))

    bridge.cleanup_task(wo_id)
    return claim_result


def test_polling_no_result(bridge: OpenClawBridge):
    """Test polling when no result.json exists yet."""
    print("\n--- Test: Polling (No Result) ---")
    wo_id = "WO-POLL-NO-RESULT"
    bridge.create_task_card({"work_order_id": wo_id, "expected_output": "test"})
    # Single check (not blocking)
    result = bridge.poll_results_once(wo_id)
    test("Poll returns 'not_found' when no result.json",
         result["status"] == "not_found", str(result.get("status")))

    bridge.cleanup_task(wo_id)


def test_result_manifest(bridge: OpenClawBridge):
    """Test writing a result manifest and polling finds it."""
    print("\n--- Test: Result Manifest ---")
    wo_id = "WO-INTEGRATION-TEST-A"

    # Write a valid result.json
    from app.services.openclaw_bridge import _artifact_dir as get_artifact_dir
    artifacts_dir = get_artifact_dir(wo_id)
    os.makedirs(artifacts_dir, exist_ok=True)
    result_path = os.path.join(artifacts_dir, "result.json")

    result_manifest = {
        "work_order_id": wo_id,
        "status": "completed",
        "result_summary": "已根据 FAQ 生成回答草稿，覆盖用户 2/3 问题",
        "artifacts": [
            {
                "name": "customer-response-draft.md",
                "path": os.path.join(artifacts_dir, "customer-response-draft.md"),
                "type": "markdown",
            }
        ],
        "confidence": 0.87,
        "unresolved_questions": ["用户还问了 API 接入时间"],
        "recommended_follow_up": "建议 Founder 审阅后发送",
        "metadata": {
            "runtime": "openclaw",
            "agent": "customer-support-agent",
            "tokens_used": 450,
        },
        "completed_at": "2026-05-29T18:30:00Z",
    }

    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result_manifest, f, ensure_ascii=False, indent=2)

    # Poll for it (single check)
    poll_result = bridge.poll_results_once(wo_id)
    test("Poll finds result with status 'completed'",
         poll_result["status"] == "completed", str(poll_result.get("status")))
    test("Result contains artifacts array",
         "artifacts" in poll_result.get("result", {}))
    test("Result contains confidence",
         poll_result.get("result", {}).get("confidence") == 0.87)
    test("Result contains unresolved_questions",
         bool(poll_result.get("result", {}).get("unresolved_questions")))

    state = bridge.get_task_state(wo_id)
    test("State is 'completed' after result found",
         state == "completed", state)

    # Clean up
    bridge.cleanup_task(wo_id)

    return result_manifest


def test_malformed_result(bridge: OpenClawBridge):
    """Test malformed result.json detection."""
    print("\n--- Test: Malformed Result ---")
    wo_id = "WO-INTEGRATION-TEST-BAD"
    bridge.create_task_card({"work_order_id": wo_id, "expected_output": "test"})

    # Write invalid JSON
    from app.services.openclaw_bridge import _artifact_dir as get_artifact_dir
    artifacts_dir = get_artifact_dir(wo_id)
    os.makedirs(artifacts_dir, exist_ok=True)
    with open(os.path.join(artifacts_dir, "result.json"), "w") as f:
        f.write("not valid json {{{")

    poll_result = bridge.poll_results_once(wo_id)
    test("Malformed JSON → status 'needs_review'",
         poll_result["status"] == "needs_review", str(poll_result.get("status")))
    test("Errors list present in result",
         bool(poll_result.get("errors")),
         str(poll_result.get("errors")))

    bridge.cleanup_task(wo_id)
    # Clean up artifacts dir
    import shutil
    shutil.rmtree(artifacts_dir, ignore_errors=True)


def test_missing_fields_result(bridge: OpenClawBridge):
    """Test result with missing required fields."""
    print("\n--- Test: Missing Required Fields ---")
    wo_id = "WO-INTEGRATION-TEST-MISSING"
    bridge.create_task_card({"work_order_id": wo_id, "expected_output": "test"})

    from app.services.openclaw_bridge import _artifact_dir as get_artifact_dir
    artifacts_dir = get_artifact_dir(wo_id)
    os.makedirs(artifacts_dir, exist_ok=True)
    # Missing 'status' and 'result_summary'
    with open(os.path.join(artifacts_dir, "result.json"), "w", encoding="utf-8") as f:
        json.dump({"work_order_id": wo_id}, f)

    poll_result = bridge.poll_results_once(wo_id)
    test("Missing fields → status 'needs_review'",
         poll_result["status"] == "needs_review", str(poll_result.get("status")))
    test("Multiple errors reported",
         len(poll_result.get("errors", [])) >= 2)

    bridge.cleanup_task(wo_id)
    import shutil
    shutil.rmtree(artifacts_dir, ignore_errors=True)


def test_timeout(bridge: OpenClawBridge):
    """Test timeout when no result appears."""
    print("\n--- Test: Timeout ---")
    wo_id = "WO-INTEGRATION-TEST-TIMEOUT"
    bridge.create_task_card({"work_order_id": wo_id, "expected_output": "test"})

    start = time.time()
    poll_result = bridge.poll_results(wo_id, timeout=5, poll_interval=1)
    elapsed = time.time() - start

    test("Timeout after 5s",
         poll_result["status"] == "timeout", str(poll_result.get("status")))
    test("Elapsed time ≈ 5s",
         4 <= elapsed <= 10, f"{elapsed:.1f}s")

    bridge.cleanup_task(wo_id)


def test_execution_mode_handler():
    """Test that openclaw_bridge_v2 handler is registered."""
    print("\n--- Test: Execution Mode Handler ---")
    test("openclaw_bridge_v2 in EXECUTION_HANDLERS",
         "openclaw_bridge_v2" in EXECUTION_HANDLERS)

    handler = EXECUTION_HANDLERS["openclaw_bridge_v2"]
    result = handler({
        "work_order_id": "WO-HANDLER-TEST",
        "goal_session_id": "GS-TEST",
        "product_line_id": "test",
        "task_type": "customer_response",
        "input_context": "test context",
        "expected_output": "test output",
        "risk_level": "low",
    })
    test("Handler returns status 'openclaw_dispatched'",
         result["status"] == "openclaw_dispatched", str(result.get("status")))
    test("Handler returns card_id",
         bool(result.get("card_id")))
    test("Handler returns execution_state with dispatched_at",
         bool(result.get("execution_state", {}).get("dispatched_to_openclaw")))

    # Clean up
    bridge = OpenClawBridge()
    bridge.cleanup_task("WO-HANDLER-TEST")


def test_callback_service():
    """Test the callback service functions."""
    print("\n--- Test: Callback Service ---")

    # API key validation
    test("Valid API key accepted",
         validate_api_key("oc-test-key-change-me"))
    test("Invalid API key rejected",
         not validate_api_key("wrong-key"))

    # Body validation
    test("Valid body passes",
         len(validate_callback_body({"status": "completed"})) == 0)
    test("Empty body fails",
         len(validate_callback_body({})) > 0)
    test("Invalid status fails",
         len(validate_callback_body({"status": "invalid_status"})) > 0)

    # Idempotency
    test("completed → completed is OK",
         check_idempotent({"status": "completed"}, "completed") is None)
    test("completed → failed rejected without force",
         check_idempotent({"status": "completed"}, "failed") is not None)
    test("completed → failed accepted with force",
         check_idempotent({"status": "completed"}, "failed", force=True) is None)
    test("in_progress → completed is OK",
         check_idempotent({"status": "in_progress"}, "completed") is None)

    # Apply callback
    wo = {"work_order_id": "WO-CB-TEST", "status": "in_progress"}
    applied = apply_callback_to_work_order(wo, {
        "status": "completed",
        "result_summary": "done",
        "artifacts": [{"name": "test.txt", "path": "/tmp/test.txt", "type": "text"}],
        "confidence": 0.95,
    })
    test("Status updated to completed",
         applied["wo_updates"]["status"] == "completed")
    test("Result summary set",
         applied["wo_updates"]["result_summary"] == "done")
    test("Artifacts stored",
         len(applied["artifacts"]) == 1)
    test("Execution log entry created",
         bool(applied["execution_log_entry"]["event"]))


def test_full_work_order_flow():
    """Test the full flow: create WO via DB → dispatch via executor → backfill."""
    print("\n--- Test: Full Work Order Flow ---")
    session = get_sync_session()
    try:
        wo_id = f"WO-FLOW-{uuid.uuid4().hex[:6].upper()}"
        wo = WorkOrder(
            work_order_id=wo_id,
            goal_session_id="GS-FLOW",
            product_line_id="test",
            skill_id="customer_support",
            task_type="customer_response",
            execution_mode="openclaw_bridge_v2",
            input_context="test input",
            expected_output="response-draft.md",
            risk_level="low",
            status="routed",
        )
        session.add(wo)
        session.commit()
        print(f"  Created WO: {wo_id}")

        # Execute via work_order_executor
        from app.services.work_order_executor import execute_work_order
        exec_result = execute_work_order(wo_id)
        test("Executor returns result",
             exec_result is not None)
        wo_status = exec_result.get("work_order", {}).get("status", "")
        test("WO status becomes 'in_progress' after dispatch",
             wo_status == "in_progress", str(wo_status))

        # Verify task card in inbox
        bridge = OpenClawBridge()
        state = bridge.get_task_state(wo_id)
        test("Task card in inbox after dispatch",
             state in ("dispatched", "claimed"),
             f"state={state}")

        # Simulate claim + result
        bridge.simulate_claim(wo_id)
        from app.services.openclaw_bridge import _artifact_dir as get_artifact_dir
        artifacts_dir = get_artifact_dir(wo_id)
        os.makedirs(artifacts_dir, exist_ok=True)
        result_manifest = {
            "work_order_id": wo_id,
            "status": "completed",
            "result_summary": "Flow test completed successfully",
            "artifacts": [
                {"name": "response.txt", "path": os.path.join(artifacts_dir, "response.txt"), "type": "text"}
            ],
            "confidence": 0.95,
        }
        with open(os.path.join(artifacts_dir, "result.json"), "w", encoding="utf-8") as f:
            json.dump(result_manifest, f)

        # Poll for result
        poll_result = bridge.poll_results_once(wo_id)
        test("Poll finds result",
             poll_result["status"] == "completed", str(poll_result.get("status")))

        # Clean up
        bridge.cleanup_task(wo_id)
        import shutil
        shutil.rmtree(artifacts_dir, ignore_errors=True)

    finally:
        session.close()


def test_callback_endpoint_mock():
    """Test the callback endpoint logic without actually starting the server."""
    print("\n--- Test: Callback Endpoint Logic ---")
    session = get_sync_session()
    try:
        wo_id = f"WO-CALLBACK-{uuid.uuid4().hex[:6].upper()}"
        wo = WorkOrder(
            work_order_id=wo_id,
            goal_session_id="GS-CALLBACK",
            product_line_id="test",
            skill_id="customer_support",
            task_type="customer_response",
            execution_mode="openclaw_bridge_v2",
            input_context="test input",
            expected_output="test output",
            risk_level="low",
            status="in_progress",
        )
        session.add(wo)
        session.commit()

        # Simulate what the callback endpoint does
        from app.services.openclaw_callback import (
            apply_callback_to_work_order,
            build_execution_log_entry,
        )

        # Read WO
        wo = session.query(WorkOrder).filter_by(work_order_id=wo_id).first()

        callback_body = {
            "status": "completed",
            "result_summary": "Callback test successful",
            "output_path": f"~/.ai-company-os/artifacts/{wo_id}/",
            "artifacts": [
                {"name": "result.md", "path": f"~/.ai-company-os/artifacts/{wo_id}/result.md", "type": "markdown"}
            ],
            "confidence": 0.92,
            "unresolved_questions": [],
            "recommended_follow_up": "None",
            "metadata": {"runtime": "openclaw", "agent": "test-agent"},
        }

        wo_dict = wo.to_dict()
        applied = apply_callback_to_work_order(wo_dict, callback_body)

        # Apply updates
        for key, value in applied["wo_updates"].items():
            setattr(wo, key, value)

        # Append execution log
        existing_log = []
        if wo.execution_log_json:
            try:
                existing_log = json.loads(wo.execution_log_json)
            except Exception:
                existing_log = []
        existing_log.append(applied["execution_log_entry"])
        wo.execution_log_json = json.dumps(existing_log, ensure_ascii=False)
        wo.completed_at = applied["wo_updates"].get("completed_at")

        session.commit()

        # Verify
        wo = session.query(WorkOrder).filter_by(work_order_id=wo_id).first()
        d = wo.to_dict()
        test("WO status updated to completed",
             d["status"] == "completed", str(d["status"]))
        test("result_summary set",
             d["result_summary"] == "Callback test successful")
        test("artifacts_json stored",
             bool(d.get("artifacts_json")))
        test("execution_log_json has callback event",
             "openclaw_completed_via_callback" in (d.get("execution_log_json", "") or ""))
        test("completed_at is set",
             bool(d.get("completed_at")))

        # Idempotency test: call again with same status
        wo_dict2 = wo.to_dict()
        idempotent = check_idempotent(wo_dict2, "completed")
        test("Idempotent callback passes",
             idempotent is None, str(idempotent))

        # Force update test: call with failed
        idempotent_fail = check_idempotent(wo_dict2, "failed")
        test("Non-idempotent rejected",
             idempotent_fail is not None)

        idempotent_force = check_idempotent(wo_dict2, "failed", force=True)
        test("Force override works",
             idempotent_force is None, str(idempotent_force))

    finally:
        session.close()


def test_get_tasks(bridge: OpenClawBridge):
    """Test get_dispatched_tasks and get_claimed_tasks."""
    print("\n--- Test: Task Listing ---")
    # Create a few tasks
    for i in range(3):
        bridge.create_task_card({
            "work_order_id": f"WO-LIST-{i}",
            "expected_output": f"test {i}",
            "task_type": "research",
        })

    dispatched = bridge.get_dispatched_tasks()
    test("get_dispatched_tasks returns tasks",
         len(dispatched) >= 3, f"got {len(dispatched)}")

    # Claim one
    bridge.simulate_claim("WO-LIST-0")
    claimed = bridge.get_claimed_tasks()
    test("get_claimed_tasks returns claimed task",
         len(claimed) >= 1, f"got {len(claimed)}")

    all_tasks = bridge.get_all_tasks()
    test("get_all_tasks has dispatched key",
         "dispatched" in all_tasks)
    test("get_all_tasks has claimed key",
         "claimed" in all_tasks)

    # Clean up
    for i in range(3):
        bridge.cleanup_task(f"WO-LIST-{i}")


def run_all():
    """Run all tests."""
    print("=" * 60)
    print(" v0.13 OpenClaw Bridge v2 — Integration Test Suite")
    print("=" * 60)

    setup_module()
    bridge = test_bridge_creation()

    test_create_task_card(bridge)
    test_claim_lifecycle(bridge)
    test_polling_no_result(bridge)
    test_result_manifest(bridge)
    test_malformed_result(bridge)
    test_missing_fields_result(bridge)
    test_timeout(bridge)
    test_execution_mode_handler()
    test_callback_service()
    test_full_work_order_flow()
    test_callback_endpoint_mock()
    test_get_tasks(bridge)

    print("\n" + "=" * 60)
    total = PASS + FAIL
    print(f" Results: {PASS}/{total} passed, {FAIL}/{total} failed")
    if FAIL > 0:
        print(" ❌ SOME TESTS FAILED")
    else:
        print(" ✅ ALL TESTS PASSED")
    print("=" * 60)
    return FAIL == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
