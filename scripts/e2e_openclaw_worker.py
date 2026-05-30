#!/usr/bin/env python3
"""
v0.14 OpenClaw Worker Real Execution — E2E 验收

全流程：
  1. 创建 WO (echo_test) → 路由 → Dispatch → inbox
  2. 运行 Worker (一回合)
  3. 验证 claim + result.json
  4. 回调 API 回填 WO
  5. 验证 WO status = completed
  6. 再次创建 WO (read_context_and_write_summary)
  7. Worker 执行 LLM 摘要
  8. 验证 summary.md 产物

用法：
  cd backend/ && python3 ../scripts/e2e_openclaw_worker.py
"""
import json
import os
import sys
import time

BACKEND_URL = "http://localhost:8001"

PASS = 0
FAIL = 0


def api(method: str, path: str, data: dict = None) -> dict:
    import urllib.request
    url = f"{BACKEND_URL}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"_error": f"HTTP {e.code}", "_detail": e.read().decode()[:300]}
    except Exception as e:
        return {"_error": str(e)}


def test(name: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} — {detail}")


def step(title: str):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


# ── 清空历史 Inbox/Working (防止干扰) ──
def clean_inbox():
    openclaw_dir = os.path.expanduser("~/.ai-company-os/openclaw")
    for sub in ["inbox", "working"]:
        d = os.path.join(openclaw_dir, sub)
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith(".task.json"):
                    os.remove(os.path.join(d, f))


# ── 主测试 ──

def run():
    global PASS, FAIL
    clean_inbox()

    step("1. 创建 WO (echo_test) → 路由 → Dispatch → Inbox")

    wo = api("POST", "/api/v1/work-orders", {
        "skill_id": "openclaw_external_agent",
        "task_type": "echo_test",
        "execution_mode": "openclaw_bridge_v2",
        "input_context": "OpenClaw Worker E2E Test — echo test verification",
        "expected_output": "echo_output.txt",
        "risk_level": "low",
    })
    wo_id = wo.get("work_order_id", "")
    test("WO 创建成功", wo.get("status") == "created", str(wo.get("status")))
    test("WO ID 生成", bool(wo_id), wo_id)
    test("execution_mode = openclaw_bridge_v2", wo.get("execution_mode") == "openclaw_bridge_v2")

    # Route + Execute via executor
    route_resp = api("POST", f"/api/v1/work-orders/{wo_id}/route")
    test("路由成功", route_resp.get("status") == "routed", str(route_resp.get("status")))

    # Use executor directly
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
    from app.services.work_order_executor import execute_work_order

    exec_result = execute_work_order(wo_id)
    exec_status = exec_result.get("execution_result", {}).get("status", "")
    test("Executor 返回 openclaw_dispatched", exec_status == "openclaw_dispatched", str(exec_status))

    # Verify inbox
    inbox_dir = os.path.expanduser("~/.ai-company-os/openclaw/inbox")
    inbox_files = [f for f in os.listdir(inbox_dir) if wo_id in f]
    test("Task card 在 inbox", len(inbox_files) > 0, str(inbox_files))

    step("2. 运行 Worker (一回合)")

    from app.services.openclaw_worker.worker import find_pending_tasks, process_task

    pending = find_pending_tasks()
    test("Worker 找到待处理任务", len(pending) > 0, str(len(pending)))

    if pending:
        result = process_task(pending[0])
        test("Worker 执行完成", result["status"] == "completed", str(result["status"]))

    step("3. 验证 Claim + Result Manifest")

    working_dir = os.path.expanduser("~/.ai-company-os/openclaw/working")
    working_files = [f for f in os.listdir(working_dir) if wo_id in f]
    test("Task card 移入 working", len(working_files) > 0, str(working_files))

    artifacts_dir = os.path.expanduser(f"~/.ai-company-os/artifacts/{wo_id}")
    result_json = os.path.join(artifacts_dir, "result.json")
    test("result.json 已写入", os.path.exists(result_json), result_json)

    if os.path.exists(result_json):
        with open(result_json) as f:
            manifest = json.load(f)
        test("Manifest 包含 work_order_id", manifest.get("work_order_id") == wo_id)
        test("Manifest 包含 steps", "steps" in manifest, str(len(manifest.get("steps", []))))
        test("Manifest 包含 executor", bool(manifest.get("executor")))
        test("Manifest 包含 artifacts", len(manifest.get("artifacts", [])) > 0)
        test("Echo output 已生成",
             os.path.exists(os.path.join(artifacts_dir, "echo_output.txt")),
             os.path.join(artifacts_dir, "echo_output.txt"))

    step("4. Callback API → WO 回填")

    cb_body = {
        "status": "completed",
        "result_summary": f"Worker 执行成功 — 详见 artifacts/{wo_id}/",
        "output_path": artifacts_dir,
        "artifacts": [{"name": "echo_output.txt", "path": os.path.join(artifacts_dir, "echo_output.txt"), "type": "text"}],
        "confidence": 1.0,
        "api_key": "oc-test-key-change-me",
    }
    cb_resp = api("POST", f"/api/v1/work-orders/{wo_id}/openclaw-callback", cb_body)
    test("Callback 返回 accepted", cb_resp.get("status") == "accepted", str(cb_resp.get("status")))

    wo_check = api("GET", f"/api/v1/work-orders/{wo_id}")
    test("WO status = completed", wo_check.get("status") == "completed", str(wo_check.get("status")))
    test("result_summary 已回填", bool(wo_check.get("result_summary")), wo_check.get("result_summary", "")[:50])

    step("5. 创建 WO (read_context_and_write_summary) → Worker → LLM 摘要")

    wo2 = api("POST", "/api/v1/work-orders", {
        "skill_id": "openclaw_external_agent",
        "task_type": "read_context_and_write_summary",
        "execution_mode": "openclaw_bridge_v2",
        "input_context": (
            "AI Company OS 是一个基于 Hermes Agent 的 CEO 编排系统。\n"
            "核心能力包括：\n"
            "1. Work Order 系统 — 创建、路由、执行、回填闭环\n"
            "2. OpenClaw Bridge — Inbox/Outbox 文件协议 + Callback API\n"
            "3. Product Line Agents — 6 条产品线自动周报\n"
            "4. Launch Pipeline — 销售页自动生成\n"
            "5. Code Bridge — 代码变更审批流\n\n"
            "v0.13 完成了 OpenClaw Bridge Real Callback MVP，\n"
            "v0.14 的目标是让 OpenClaw Worker 真实执行任务并回填结果。"
        ),
        "expected_output": "summary.md",
        "risk_level": "low",
    })
    wo2_id = wo2.get("work_order_id", "")
    test("WO2 创建成功", bool(wo2_id), str(wo2_id))

    # Route + execute
    api("POST", f"/api/v1/work-orders/{wo2_id}/route")
    execute_work_order(wo2_id)

    # Run worker
    pending2 = find_pending_tasks()
    test("Worker 找到 WO2", len(pending2) > 0, str(len(pending2)))

    if pending2:
        result2 = process_task(pending2[0])
        test("Worker 执行 WO2 完成", result2["status"] == "completed", str(result2.get("status")))

    # Verify summary.md
    artifacts_dir2 = os.path.expanduser(f"~/.ai-company-os/artifacts/{wo2_id}")
    summary_md = os.path.join(artifacts_dir2, "summary.md")
    result_json2 = os.path.join(artifacts_dir2, "result.json")

    test("summary.md 已生成", os.path.exists(summary_md), summary_md)
    test("result.json 已生成", os.path.exists(result_json2), result_json2)

    if os.path.exists(result_json2):
        with open(result_json2) as f:
            manifest2 = json.load(f)
        test("WO2 Manifest 包含 steps", len(manifest2.get("steps", [])) > 0, str(len(manifest2["steps"])))
        test("WO2 Manifest 包含 confidence > 0", manifest2.get("confidence", 0) > 0, str(manifest2.get("confidence")))

    if os.path.exists(summary_md):
        content = open(summary_md).read()
        test("summary.md 内容非空", len(content) > 50, f"{len(content)} chars")
        test("summary.md 包含 AI Company OS", "AI Company OS" in content, "关键词匹配")
        print(f"\n  --- summary.md preview ---")
        for line in content.split("\n")[:8]:
            print(f"  {line}")

    step("6. Callback → WO2 回填")

    cb_body2 = {
        "status": "completed",
        "result_summary": "LLM 摘要已生成",
        "output_path": artifacts_dir2,
        "api_key": "oc-test-key-change-me",
    }
    api("POST", f"/api/v1/work-orders/{wo2_id}/openclaw-callback", cb_body2)
    wo2_check = api("GET", f"/api/v1/work-orders/{wo2_id}")
    test("WO2 status = completed", wo2_check.get("status") == "completed", str(wo2_check.get("status")))

    # ── Final Summary ──
    step(f"结果: {PASS}/{PASS+FAIL} 通过, {FAIL}/{PASS+FAIL} 失败")
    if FAIL == 0:
        print("\n 🎉 v0.14 全流程验收通过！")
        print(f"")
        print(f"  Worker 已验证:")
        print(f"    ✅ echo_test — 纯逻辑执行")
        print(f"    ✅ read_context_and_write_summary — LLM 摘要生成")
        print(f"    ✅ Inbox → Claim → Execute → result.json → Callback → WO 回填")
    else:
        print("\n ❌ 存在失败项")


if __name__ == "__main__":
    run()
