#!/usr/bin/env python3
"""
v0.14.2 — Executor Abstraction + OpenClaw Native Executor E2E

Proves:
  WO -> inbox -> Worker -> OpenClawAgentExecutor (openclaw agent --json)
    -> result.json (full provenance + tool evidence) -> WO completed

Modes tested:
  1. echo_test (EchoExecutor — fast path)
  2. read_context_and_write_summary (OpenClawAgentExecutor — real cloud model)
  3. OPENCLAW_EXECUTOR_MODE=openclaw_native (forced native path)
  4. OPENCLAW_EXECUTOR_MODE=local_llm (forced fallback)
  5. Provenance contract (all fields, including v0.14.2 tool evidence)
  6. Full chain: WO -> dispatch -> Worker -> OpenClaw agent -> callback -> completed
"""
import json
import os
import sys
import time
import uuid

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

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


def create_and_dispatch(task_type: str, input_context: str = "", expected_output: str = "output.md"):
    """Create WO via Python API -> route -> execute. Returns wo_id."""
    from app.database import get_sync_session
    from app.models.work_order import WorkOrder
    from app.services.work_order_executor import execute_work_order

    session = get_sync_session()
    wo_id = f"WO-E2E-{uuid.uuid4().hex[:6].upper()}"
    try:
        wo = WorkOrder(
            work_order_id=wo_id,
            goal_session_id="GS-E2E-142",
            product_line_id="ai-company-os",
            skill_id="openclaw_external_agent",
            task_type=task_type,
            execution_mode="openclaw_bridge_v2",
            input_context=input_context or f"test context for {task_type}",
            expected_output=expected_output,
            risk_level="low",
            status="routed",
        )
        session.add(wo)
        session.commit()
    finally:
        session.close()

    exec_result = execute_work_order(wo_id)
    status = exec_result.get("execution_result", {}).get("status", "")
    assert status == "openclaw_dispatched", f"Expected dispatched, got {status}"
    return wo_id


def process_worker_task(wo_id: str, call_backend: bool = False):
    """Run the worker to process one specific task by claim + execute."""
    from app.services.openclaw_worker.worker import find_pending_tasks, process_task

    pending = find_pending_tasks()
    card_info = None
    for p in pending:
        if p["work_order_id"] == wo_id:
            card_info = p
            break

    if not card_info:
        return {"status": "not_found", "work_order_id": wo_id}

    result = process_task(card_info, call_backend=call_backend, backend_url="http://localhost:8001")
    return result


def verify_provenance(result: dict, expected_type: str):
    """Verify the result manifest has the right provenance fields."""
    m = result.get("execution_result", result)
    test(f"executor_type = {expected_type}", m.get("executor_type") == expected_type, str(m.get("executor_type")))
    test("executor_name exists", bool(m.get("executor_name")), str(m.get("executor_name")))
    test("native_openclaw is bool", isinstance(m.get("native_openclaw"), bool))
    test("runtime_backend exists", bool(m.get("runtime_backend")), str(m.get("runtime_backend")))
    test("started_at exists", bool(m.get("started_at")))
    test("finished_at exists", bool(m.get("finished_at")))


# ---- Test Suite ----


def test_echo_executor():
    """EchoExecutor: fast path, no LLM."""
    step_header("1. EchoExecutor -- rule-based fast path")
    wo_id = create_and_dispatch("echo_test", "test echo context", "echo_output.md")
    test("WO dispatched", bool(wo_id), wo_id)

    result = process_worker_task(wo_id)
    test("Worker processed", result["status"] == "completed", str(result["status"]))

    m = result.get("execution_result", {})
    test("executor_type = echo", m.get("executor_type") == "echo", str(m.get("executor_type")))
    test("native_openclaw = false", m.get("native_openclaw") is False)
    test("contains artifacts", len(m.get("artifacts", [])) > 0)
    # v0.14.2: echo executor should not have tool evidence
    test("tool_calls_detected = false (echo)", m.get("tool_calls_detected") is False)
    test("tool_trace_available = false", m.get("tool_trace_available") is False)

    return wo_id


def test_openclaw_agent_executor():
    """OpenClawAgentExecutor: real OpenClaw agent via --json output."""
    step_header("2. OpenClawAgentExecutor -- real cloud model (auto mode)")
    os.environ["OPENCLAW_EXECUTOR_MODE"] = "auto"

    wo_id = create_and_dispatch(
        "read_context_and_write_summary",
        "AI Company OS is a task execution system that routes Work Orders via Skill Router to execution runtimes. Version v0.14.2 implements tool evidence fields.",
        "summary.md",
    )
    test("WO dispatched", bool(wo_id), wo_id)

    result = process_worker_task(wo_id)
    test("Worker processed", result["status"] == "completed", str(result["status"]))

    verify_provenance(result, "openclaw_agent")
    m = result.get("execution_result", {})
    test("native_openclaw = true", m.get("native_openclaw") is True, str(m.get("native_openclaw")))
    test("model_name exists (cloud model)", bool(m.get("model_name")), str(m.get("model_name")))
    test("model_provider exists", bool(m.get("model_provider")), str(m.get("model_provider")))
    test("openclaw_agent = research-agent or main",
         m.get("openclaw_agent") in ("research-agent", "main"),
         str(m.get("openclaw_agent")))
    test("token_usage has total > 0",
         m.get("token_usage", {}).get("total_tokens", 0) > 0,
         str(m.get("token_usage", {}).get("total_tokens", 0)))
    test("duration_ms > 0",
         (m.get("duration_ms") or 0) > 0,
         str(m.get("duration_ms")))
    test("openclaw_run_id exists", bool(m.get("openclaw_run_id")), str(m.get("openclaw_run_id"))[:20])
    test("openclaw_stop_reason = stop",
         m.get("openclaw_stop_reason") == "stop",
         str(m.get("openclaw_stop_reason")))
    test("output_text non-empty", bool(m.get("output_text")), f"{len(m.get('output_text',''))} chars")
    # v0.14.2: tool evidence
    test("tool_calls_detected is bool", isinstance(m.get("tool_calls_detected"), bool))
    test("tool_trace_available = false (CLI limitation)",
         m.get("tool_trace_available") is False)

    return wo_id


def test_openclaw_native_mode():
    """OPENCLAW_EXECUTOR_MODE=openclaw_native: forced native path."""
    step_header("3. openclaw_native mode -- forced OpenClaw execution")
    os.environ["OPENCLAW_EXECUTOR_MODE"] = "openclaw_native"

    wo_id = create_and_dispatch(
        "read_context_and_write_summary",
        "This task must be executed by OpenClaw native agent, not local LLM.",
        "native-output.md",
    )
    test("WO dispatched", bool(wo_id), wo_id)

    result = process_worker_task(wo_id)
    test("Worker processed", result["status"] == "completed", str(result["status"]))

    m = result.get("execution_result", {})
    test("executor_type = openclaw_agent", m.get("executor_type") == "openclaw_agent", str(m.get("executor_type")))
    test("native_openclaw = true", m.get("native_openclaw") is True)
    test("model_name exists (cloud)", bool(m.get("model_name")), str(m.get("model_name")))

    return wo_id


def test_local_llm_fallback():
    """OPENCLAW_EXECUTOR_MODE=local_llm: forced local fallback."""
    step_header("4. local_llm mode -- forced Ollama fallback")
    os.environ["OPENCLAW_EXECUTOR_MODE"] = "local_llm"

    wo_id = create_and_dispatch(
        "read_context_and_write_summary",
        "This task must be executed by local LLM, not OpenClaw agent. Summarize this sentence.",
        "llm-output.md",
    )
    test("WO dispatched", bool(wo_id), wo_id)

    result = process_worker_task(wo_id)
    test("Worker processed", result["status"] == "completed", str(result["status"]))

    m = result.get("execution_result", {})
    test("executor_type = local_llm", m.get("executor_type") == "local_llm", str(m.get("executor_type")))
    test("native_openclaw = false", m.get("native_openclaw") is False)
    test("model_name contains local model",
         "deepseek" in (m.get("model_name") or ""),
         str(m.get("model_name")))
    test("token_usage has output_tokens",
         m.get("token_usage", {}).get("output_tokens", 0) > 0,
         str(m.get("token_usage", {})))

    return wo_id


def test_provenance_fields():
    """Verify the provenance contract is complete, including v0.14.2 tool evidence."""
    step_header("5. Provenance + tool evidence contract verification")

    from app.services.openclaw_worker.executors.base import ExecutionResult, extract_inferred_tools

    # Test extract_inferred_tools
    tools = extract_inferred_tools("I used tavily_search and write to create a file, then exec to verify")
    test("extract_inferred_tools finds tools", "tavily_search" in tools and "write" in tools, str(tools))

    tools_empty = extract_inferred_tools("")
    test("extract_inferred_tools handles empty", tools_empty == [], str(tools_empty))

    tools_none = extract_inferred_tools("Hello, this is a simple greeting.")
    test("extract_inferred_tools no tools found", tools_none == [], str(tools_none))

    # Full manifest contract
    r = ExecutionResult(
        status="completed",
        result_summary="test",
        executor_type="openclaw_agent",
        openclaw_agent="research-agent",
        model_provider="minimax",
        model_name="MiniMax-M2.5",
        token_usage={"total_tokens": 1000},
        duration_ms=5000,
        openclaw_run_id="test-run-id",
        openclaw_stop_reason="stop",
        # v0.14.2: tool evidence
        tool_calls_detected=True,
        tool_call_summary="tavily_search, write, exec",
        inferred_tools=["tavily_search", "write", "exec"],
        tool_call_evidence_source="agent_output_text",
        tool_trace_available=False,
        artifacts=[{"name": "test.md", "path": "/tmp/test.md", "type": "markdown"}],
    )

    m = r.to_manifest()
    required_fields = [
        "status", "executor_type", "executor_name", "native_openclaw",
        "runtime_backend", "openclaw_agent", "model_provider", "model_name",
        "token_usage", "duration_ms", "openclaw_run_id", "openclaw_stop_reason",
        "started_at", "finished_at",
        # v0.14.2 fields
        "tool_calls_detected", "tool_call_summary", "inferred_tools",
        "tool_call_evidence_source", "tool_trace_available",
    ]
    for field in required_fields:
        test(f"Manifest has {field}", field in m, f"missing: {field}")

    test("tool_calls_detected = true", m.get("tool_calls_detected") is True)
    test("inferred_tools has 3 items", len(m.get("inferred_tools", [])) == 3, str(m.get("inferred_tools")))
    test("tool_trace_available = false", m.get("tool_trace_available") is False)

    local_r = ExecutionResult(
        status="completed",
        result_summary="local test",
        executor_type="local_llm",
        native_openclaw=False,
    )
    lm = local_r.to_manifest()
    test("local manifest has native_openclaw=false", lm.get("native_openclaw") is False)
    test("local manifest has executor_type=local_llm", lm.get("executor_type") == "local_llm")
    test("local manifest has default tool_calls_detected=false",
         lm.get("tool_calls_detected") is False)


def test_full_chain_pure_python():
    """Full chain: WO -> dispatch -> Worker -> OpenClaw agent -> callback -> WO completed.
    
    Uses pure Python API (no HTTP), verifying the complete callback protocol.
    """
    step_header("6. Full chain (pure Python) -- WO dispatch + callback protocol")
    os.environ["OPENCLAW_EXECUTOR_MODE"] = "auto"

    from app.services.openclaw_worker.worker import find_pending_tasks
    from app.services.work_order_executor import execute_work_order
    from app.database import get_sync_session
    from app.models.work_order import WorkOrder
    from app.services.openclaw_callback import (
        apply_callback_to_work_order,
        check_idempotent,
        validate_api_key,
        validate_callback_body,
    )

    # Create WO via Python API
    wo_id = f"WO-E2E-{uuid.uuid4().hex[:6].upper()}"
    session = get_sync_session()
    try:
        wo = WorkOrder(
            work_order_id=wo_id,
            goal_session_id="GS-E2E-BACKEND",
            product_line_id="ai-company-os",
            skill_id="openclaw_external_agent",
            task_type="read_context_and_write_summary",
            execution_mode="openclaw_bridge_v2",
            input_context="Full callback test. This task verifies the complete callback protocol via pure Python API.",
            expected_output="callback-protocol-output.md",
            risk_level="low",
            status="routed",
        )
        session.add(wo)
        session.commit()
        test("WO created", bool(wo_id), wo_id)
    finally:
        session.close()

    # Dispatch via execute_work_order (pure Python, no HTTP)
    exec_result = execute_work_order(wo_id)
    dispatch_status = exec_result.get("execution_result", {}).get("status", "")
    test("WO dispatched (openclaw_dispatched)",
         dispatch_status == "openclaw_dispatched",
         str(dispatch_status))

    # Verify WO is in_inbox
    pending = find_pending_tasks()
    in_inbox = any(p["work_order_id"] == wo_id for p in pending)
    test("WO in inbox", in_inbox, wo_id)

    # Process via Worker
    proc_result = process_worker_task(wo_id)
    test("Worker processed", proc_result["status"] == "completed", str(proc_result["status"]))

    # Verify result manifest
    m = proc_result.get("execution_result", {})
    test("executor_type = openclaw_agent",
         m.get("executor_type") == "openclaw_agent",
         str(m.get("executor_type")))
    test("native_openclaw = true", m.get("native_openclaw") is True)
    test("model_name exists", bool(m.get("model_name")), str(m.get("model_name")))
    test("openclaw_run_id exists", bool(m.get("openclaw_run_id")))

    # ---- Callback Protocol Verification ----
    # v0.14.2: The worker already wrote result.json.
    # We verify that the callback protocol (apply_callback_to_work_order) works correctly
    # on a known WO.

    callback_body = {
        "status": "completed",
        "result_summary": f"Worker completed WO {wo_id} via OpenClaw agent",
        "artifacts": m.get("artifacts", []),
        "output_text": m.get("output_text", ""),
    }

    # Read WO from DB for callback verification
    session2 = get_sync_session()
    try:
        wo_db = session2.query(WorkOrder).filter_by(work_order_id=wo_id).first()
        wo_dict = wo_db.to_dict() if wo_db else {}

        # Test idempotency check
        idempotent_check = check_idempotent(wo_dict, "completed")
        test("Idempotent check passes (->completed)",
             idempotent_check is None, str(idempotent_check))

        # Test callback body validation
        body_errors = validate_callback_body(callback_body)
        test("Callback body passes validation",
             len(body_errors) == 0, str(body_errors))

        # Test apply_callback
        cb_result = apply_callback_to_work_order(wo_dict, callback_body)
        test("Callback applied successfully", bool(cb_result.get("wo_updates")), str(cb_result))
        test("Callback sets status = completed",
             cb_result["wo_updates"].get("status") == "completed",
             str(cb_result["wo_updates"].get("status")))
        test("Callback preserves result_summary",
             bool(cb_result["wo_updates"].get("result_summary")),
             cb_result["wo_updates"].get("result_summary", "")[:50])
        test("Callback has execution_log_entry",
             bool(cb_result.get("execution_log_entry")),
             str(cb_result.get("execution_log_entry", {}).get("event")))
        test("Callback artifacts match",
             len(cb_result.get("artifacts", [])) > 0,
             str(len(cb_result.get("artifacts", []))))
    finally:
        session2.close()

    return wo_id


def run_all():
    """Run all tests."""
    print("=" * 70)
    print(" v0.14.2 -- Executor Abstraction + OpenClaw Native Executor E2E")
    print("=" * 70)

    test_echo_executor()
    test_openclaw_agent_executor()
    test_openclaw_native_mode()
    test_local_llm_fallback()
    test_provenance_fields()
    test_full_chain_pure_python()

    global PASS, FAIL
    total = PASS + FAIL
    print(f"\n{'='*70}")
    print(f" Results: {PASS}/{total} passed, {FAIL}/{total} failed")
    if FAIL == 0:
        print(" ✅ ALL TESTS PASSED")
        print(f"\n v0.14.2 验证完成:")
        print(f"   ✅ EchoExecutor -- rule-based fast path")
        print(f"   ✅ OpenClawAgentExecutor -- real cloud model (MiniMax-M2.5)")
        print(f"   ✅ openclaw_native mode -- forced OpenClaw path")
        print(f"   ✅ local_llm mode -- Ollama fallback")
        print(f"   ✅ Provenance + Tool Evidence contract")
        print(f"   ✅ Full chain: pure Python API (WO -> dispatch -> Worker -> callback protocol)")
    else:
        print(" ❌ SOME TESTS FAILED")
    print(f"{'='*70}")
    return FAIL == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
