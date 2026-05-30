#!/usr/bin/env python3
"""
v0.14.1 — OpenClaw Native Executor E2E Test

Proves:
  WO → inbox → Worker → OpenClawAgentExecutor (openclaw agent --json)
    → result.json (with full provenance) → Callback API → WO completed

Modes tested:
  1. echo_test (EchoExecutor — fast path)
  2. read_context_and_write_summary (OpenClawAgentExecutor — real cloud model)
  3. OPENCLAW_EXECUTOR_MODE=openclaw_native (forced native path)
  4. OPENCLAW_EXECUTOR_MODE=local_llm (forced fallback)
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


# ── Helper: create WO + route + execute ──

def create_and_dispatch(task_type: str, input_context: str = "", expected_output: str = "output.md"):
    """Create WO → route → execute → verify dispatched. Returns wo_id."""
    from app.database import get_sync_session
    from app.models.work_order import WorkOrder
    from app.services.work_order_executor import execute_work_order

    session = get_sync_session()
    wo_id = f"WO-E2E-{uuid.uuid4().hex[:6].upper()}"
    try:
        wo = WorkOrder(
            work_order_id=wo_id,
            goal_session_id="GS-E2E-141",
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

    # Execute
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


# ── Test Suite ──

def test_echo_executor():
    """EchoExecutor: fast path, no LLM."""
    step_header("1. EchoExecutor — rule-based fast path")
    wo_id = create_and_dispatch("echo_test", "test echo context", "echo_output.md")
    test("WO dispatched", bool(wo_id), wo_id)

    result = process_worker_task(wo_id)
    test("Worker processed", result["status"] == "completed", str(result["status"]))

    m = result.get("execution_result", {})
    test("executor_type = echo", m.get("executor_type") == "echo", str(m.get("executor_type")))
    test("native_openclaw = false", m.get("native_openclaw") is False)
    test("contains artifacts", len(m.get("artifacts", [])) > 0)

    return wo_id


def test_openclaw_agent_executor():
    """OpenClawAgentExecutor: real OpenClaw agent via --json output."""
    step_header("2. OpenClawAgentExecutor — real cloud model (auto mode)")
    import os
    os.environ["OPENCLAW_EXECUTOR_MODE"] = "auto"

    wo_id = create_and_dispatch(
        "read_context_and_write_summary",
        "AI Company OS is a task execution system that routes Work Orders via Skill Router to execution runtimes. Version v0.14.1 implements executor abstraction with OpenClaw native agent integration.",
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

    return wo_id


def test_openclaw_native_mode():
    """OPENCLAW_EXECUTOR_MODE=openclaw_native: forced native path."""
    step_header("3. openclaw_native mode — forced OpenClaw execution")
    import os
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
    step_header("4. local_llm mode — forced Ollama fallback")
    import os
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
    """Verify the provenance contract is complete."""
    step_header("5. Provenance contract verification")

    from app.services.openclaw_worker.executors.base import ExecutionResult

    r = ExecutionResult(
        status="completed",
        result_summary="test",
        executor_type="openclaw_agent",
        executor_name="OpenClawAgentExecutor",
        native_openclaw=True,
        runtime_backend="openclaw_cli",
        openclaw_agent="research-agent",
        model_provider="minimax",
        model_name="MiniMax-M2.5",
        token_usage={"total_tokens": 1000},
        duration_ms=5000,
        openclaw_run_id="test-run-id",
        openclaw_stop_reason="stop",
        artifacts=[{"name": "test.md", "path": "/tmp/test.md", "type": "markdown"}],
    )

    m = r.to_manifest()
    required_fields = [
        "status", "executor_type", "executor_name", "native_openclaw",
        "runtime_backend", "openclaw_agent", "model_provider", "model_name",
        "token_usage", "duration_ms", "openclaw_run_id", "openclaw_stop_reason",
        "started_at", "finished_at",
    ]
    for field in required_fields:
        test(f"Manifest has {field}", field in m, f"missing: {field}")

    local_r = ExecutionResult(
        status="completed",
        result_summary="local test",
        executor_type="local_llm",
        native_openclaw=False,
    )
    lm = local_r.to_manifest()
    test("local manifest has native_openclaw=false", lm.get("native_openclaw") is False)
    test("local manifest has executor_type=local_llm", lm.get("executor_type") == "local_llm")


def test_callback_with_provenance():
    """Full chain: WO → dispatch → Worker → OpenClaw agent → callback → WO completed."""
    step_header("6. Full chain with Callback API + provenance")
    import os
    os.environ["OPENCLAW_EXECUTOR_MODE"] = "auto"

    # Create and execute via backend API
    import urllib.request

    # Create WO
    body = json.dumps({
        "skill_id": "openclaw_external_agent",
        "task_type": "read_context_and_write_summary",
        "execution_mode": "openclaw_bridge_v2",
        "input_context": "Full callback test. This is a task executed by OpenClaw agent and reported via callback API.",
        "expected_output": "callback-output.md",
        "risk_level": "low",
    }).encode()
    req = urllib.request.Request("http://localhost:8001/api/v1/work-orders", data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=10) as resp:
        wo = json.loads(resp.read().decode())
    wo_id = wo["work_order_id"]
    test("WO created", bool(wo_id), wo_id)

    # Route
    route_req = urllib.request.Request(f"http://localhost:8001/api/v1/work-orders/{wo_id}/route", method="POST")
    with urllib.request.urlopen(route_req, timeout=10) as resp:
        route_result = json.loads(resp.read().decode())
    test("WO routed", route_result.get("status") == "routed", str(route_result.get("status")))

    # Execute via executor
    from app.services.work_order_executor import execute_work_order
    exec_result = execute_work_order(wo_id)
    test("WO dispatched", exec_result.get("execution_result", {}).get("status") == "openclaw_dispatched")

    # Process with callback
    result = process_worker_task(wo_id, call_backend=True)
    test("Worker processed + callback", result["status"] == "completed", str(result["status"]))

    # Verify WO status via API
    get_req = urllib.request.Request(f"http://localhost:8001/api/v1/work-orders/{wo_id}")
    with urllib.request.urlopen(get_req, timeout=10) as resp:
        wo_final = json.loads(resp.read().decode())

    test("WO status = completed via API", wo_final.get("status") == "completed", str(wo_final.get("status")))
    test("result_summary set via callback", bool(wo_final.get("result_summary")))

    # Verify provenance stored in execution_log_json
    log = wo_final.get("execution_log_json", "")
    test("execution_log has native_openclaw info",
         "native_openclaw" in (log or ""),
         log[:100])
    test("execution_log has model_name",
         "model_name" in (log or ""),
         log[:100])

    return wo_id


def run_all():
    """Run all tests."""
    print("=" * 70)
    print(" v0.14.1 — Executor Abstraction + OpenClaw Native Executor E2E")
    print("=" * 70)

    test_echo_executor()
    test_openclaw_agent_executor()
    test_openclaw_native_mode()
    test_local_llm_fallback()
    test_provenance_fields()
    test_callback_with_provenance()

    print(f"\n{'='*70}")
    total = PASS + FAIL
    print(f" Results: {PASS}/{total} passed, {FAIL}/{total} failed")
    if FAIL == 0:
        print(" ✅ ALL TESTS PASSED")
        print(f"\n v0.14.1 验证完成:")
        print(f"   ✅ EchoExecutor — rule-based fast path")
        print(f"   ✅ OpenClawAgentExecutor — 真实云端模型 (MiniMax-M2.5)")
        print(f"   ✅ openclaw_native mode — 强制 OpenClaw 路径")
        print(f"   ✅ local_llm mode — Ollama fallback")
        print(f"   ✅ Provenance 合约 — 所有字段完整")
        print(f"   ✅ 全链 callback — WO + Worker + callback + WO completed")
    else:
        print(" ❌ SOME TESTS FAILED")
    print(f"{'='*70}")
    return FAIL == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
