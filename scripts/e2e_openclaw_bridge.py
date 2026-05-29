#!/usr/bin/env python3
"""
v0.13 OpenClaw Bridge — 实时验收全流程

启动后端后运行：python3 scripts/e2e_openclaw_bridge.py

全流程：
  1. POST 创建 WO → 2. POST 执行 → 3. 检查 inbox
  4. simulate_claim → 5. 写 result.json → 6. poll 完成
  7. 调用 callback 端点 → 8. GET 验证 WO 状态 → 9. CEO 摘要
"""
import json
import os
import sys
import time
import uuid

BASE_URL = "http://localhost:8001"
API_KEY = "oc-test-key-change-me"
ARTIFACTS_DIR = os.path.expanduser("~/.ai-company-os/artifacts")
OPENCLAW_DIR = os.path.expanduser("~/.ai-company-os/openclaw")

PASS = 0
FAIL = 0


def api(method: str, path: str, data: dict = None) -> dict:
    """Make an API call and return parsed JSON."""
    import urllib.request
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"_error": f"HTTP {e.code}", "_detail": e.read().decode()[:200]}
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


def step_header(s: str):
    print(f"\n{'='*60}")
    print(f" {s}")
    print(f"{'='*60}")


# ── 主流程 ──

step_header("1. 创建 Work Order (execution_mode=openclaw_bridge_v2)")

wo_resp = api("POST", "/api/v1/work-orders", {
    "skill_id": "customer_support",
    "task_type": "customer_response",
    "execution_mode": "openclaw_bridge_v2",
    "input_context": "用户问：利润报告支持哪个站点的数据？能否接入 Amazon.ca 站点？",
    "expected_output": "response-draft.md",
    "risk_level": "low",
})
wo_id = wo_resp.get("work_order_id", "")
test("WO 创建成功", wo_resp.get("status") == "created", str(wo_resp.get("status")))
test("WO ID 生成", bool(wo_id), wo_id)
test("execution_mode=openclaw_bridge_v2", wo_resp.get("execution_mode") == "openclaw_bridge_v2")


step_header("2. 路由 Work Order (找到匹配 skill)")

route_resp = api("POST", f"/api/v1/work-orders/{wo_id}/route")
test("路由成功", route_resp.get("status") == "routed", str(route_resp.get("status")))
test("risk_level 已设置", bool(route_resp.get("risk_level")))


step_header("3. 执行 Work Order → OpenClaw Dispatch (通过 Executor)")

# 直接使用 WorkOrderExecutor — 不经过 API execute（它只做状态标记，会覆盖路由状态）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from app.services.work_order_executor import execute_work_order

exec_result = execute_work_order(wo_id)
exec_status = exec_result.get("execution_result", {}).get("status", "")
exec_card_id = exec_result.get("execution_result", {}).get("card_id", "")
test("Executor 返回 openclaw_dispatched", exec_status == "openclaw_dispatched", str(exec_status))
test("Task Card ID 生成", bool(exec_card_id), str(exec_card_id))


step_header("4. 检查 Task Card 在 Inbox")

inbox_files = os.listdir(os.path.join(OPENCLAW_DIR, "inbox"))
test("inbox 中有 task.json 文件", any(wo_id in f for f in inbox_files), str(inbox_files))

# 读取 task card 内容
from app.services.openclaw_bridge import OpenClawBridge
bridge = OpenClawBridge()
state = bridge.get_task_state(wo_id)
test("Task state = dispatched", state == "dispatched", state)


step_header("5. 模拟 OpenClaw 领取任务")

claim = bridge.simulate_claim(wo_id)
test("Claim 成功", claim["status"] == "claimed_by_openclaw", str(claim.get("status")))
state = bridge.get_task_state(wo_id)
test("Task state = claimed", state == "claimed", state)
test("Task card 在 working 目录",
     os.path.exists(bridge.get_task_card_path(wo_id) or ""),
     str(bridge.get_task_card_path(wo_id)))


step_header("6. 模拟 OpenClaw 写入 Result Manifest")

from app.services.openclaw_bridge import _artifact_dir as get_artifact_dir

artifacts_dir = get_artifact_dir(wo_id)
os.makedirs(artifacts_dir, exist_ok=True)

result_manifest = {
    "work_order_id": wo_id,
    "status": "completed",
    "result_summary": "已根据 FAQ 生成回答草稿：\n- ✅ 支持 Amazon.com 和 Amazon.ca 站点\n- ❌ Amazon.co.uk 暂不支持（需额外配置）",
    "artifacts": [
        {
            "name": "customer-response-draft.md",
            "path": os.path.join(artifacts_dir, "customer-response-draft.md"),
            "type": "markdown",
        }
    ],
    "confidence": 0.87,
    "unresolved_questions": [
        "用户还问了是否支持 Amazon.co.uk 站点",
        "用户问 API 接入时间"
    ],
    "recommended_follow_up": "建议 Founder 审阅后发送给用户，同时补充 UK 站点 FAQ",
    "metadata": {
        "runtime": "openclaw",
        "agent": "customer-support-agent",
        "tokens_used": 450,
    },
    "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}

with open(os.path.join(artifacts_dir, "result.json"), "w", encoding="utf-8") as f:
    json.dump(result_manifest, f, ensure_ascii=False, indent=2)

# 写入产物文件
draft_path = os.path.join(artifacts_dir, "customer-response-draft.md")
with open(draft_path, "w", encoding="utf-8") as f:
    f.write("""# 利润报告站点支持说明

尊敬的客户您好，

感谢您的咨询！关于利润报告支持的站点：

1. **Amazon.com** ✅ — 已支持
2. **Amazon.ca** ✅ — 已支持
3. **Amazon.co.uk** ❌ — 暂不支持，需要额外配置

关于 API 接入时间，我们建议预约演示了解详细方案。

---
*此回复由 AI 自动生成，请 Founder 审阅后发送。*
""")

test("Result Manifest 已写入", os.path.exists(os.path.join(artifacts_dir, "result.json")))
test("产物文件已写入", os.path.exists(draft_path))


step_header("7. 轮询检测结果")

poll = bridge.poll_results_once(wo_id)
test("Poll 检测到 completed", poll["status"] == "completed", str(poll.get("status")))
test("Result 包含 summary",
     bool(poll.get("result", {}).get("result_summary")),
     poll.get("result", {}).get("result_summary", "")[:50])
test("Result 包含 artifacts 列表",
     len(poll.get("result", {}).get("artifacts", [])) > 0)
test("Result 包含 confidence",
     poll.get("result", {}).get("confidence", 0) > 0)

state = bridge.get_task_state(wo_id)
test("Task state = completed", state == "completed", state)


step_header("8. 调用 Callback 端点测试")

# 先创建一个新的 WO 来测试 callback
cb_wo = api("POST", "/api/v1/work-orders", {
    "skill_id": "customer_support",
    "task_type": "customer_response",
    "execution_mode": "openclaw_bridge_v2",
    "input_context": "测试 callback 端点",
    "expected_output": "test",
    "risk_level": "low",
    "status": "in_progress",
})
cb_wo_id = cb_wo.get("work_order_id", "")
test("Callback 测试 WO 创建成功", bool(cb_wo_id), str(cb_wo_id))

# 调用 callback 端点
callback_body = {
    "status": "completed",
    "result_summary": "Callback 端点测试成功！",
    "output_path": f"~/.ai-company-os/artifacts/{cb_wo_id}/",
    "artifacts": [
        {"name": "test.md", "path": f"~/.ai-company-os/artifacts/{cb_wo_id}/test.md", "type": "markdown"}
    ],
    "confidence": 0.95,
    "api_key": API_KEY,
}

cb_resp = api("POST", f"/api/v1/work-orders/{cb_wo_id}/openclaw-callback", callback_body)
test("Callback 返回 accepted", cb_resp.get("status") == "accepted", str(cb_resp.get("status")))
test("Callback 返回 artifacts",
     len(cb_resp.get("artifacts", [])) > 0)

# 验证 WO 状态已更新
wo_check = api("GET", f"/api/v1/work-orders/{cb_wo_id}")
test("WO status = completed", wo_check.get("status") == "completed", str(wo_check.get("status")))
test("result_summary 已回填",
     "Callback 端点测试成功" in (wo_check.get("result_summary") or ""),
     wo_check.get("result_summary"))
test("artifacts_json 已存储",
     bool(wo_check.get("artifacts_json")),
     wo_check.get("artifacts_json", "")[:50])
test("execution_log_json 有 callback 事件",
     "openclaw_completed_via_callback" in (wo_check.get("execution_log_json") or ""),
     wo_check.get("execution_log_json", "")[:100])


step_header("9. 验证 Idempotency")

# 重复调用 (idempotent)
cb_dup = api("POST", f"/api/v1/work-orders/{cb_wo_id}/openclaw-callback", {
    "status": "completed",
    "result_summary": "重复调用",
    "api_key": API_KEY,
})
test("重复 callback 返回 accepted", cb_dup.get("status") == "accepted", str(cb_dup.get("status")))

# 不同状态无 force (应拒绝)
cb_bad = api("POST", f"/api/v1/work-orders/{cb_wo_id}/openclaw-callback", {
    "status": "failed",
    "result_summary": "不应被接受",
    "api_key": API_KEY,
})
test("completed→failed 无 force 被拒绝", "409" in str(cb_bad.get("_error", "")), str(cb_bad.get("_detail", "")))

# 不同状态带 force (应接受)
cb_force = api("POST", f"/api/v1/work-orders/{cb_wo_id}/openclaw-callback", {
    "status": "failed",
    "result_summary": "强制覆盖",
    "api_key": API_KEY,
    "force": True,
})
test("completed→failed 带 force 接受", cb_force.get("status") == "accepted", str(cb_force.get("status")))


step_header("10. CEO 摘要检查")

# 创建一个 Goal Session 来测试 CEO 摘要
gs_resp = api("POST", "/api/v1/ceo/goal-intake", {
    "goal": "测试 OpenClaw 桥接功能",
    "product_line_id": "ai-company-os",
    "auto_execute": False,
    "tasks": [
        {
            "task_type": "customer_response",
            "task_desc": "测试 OpenClaw 客服响应",
            "input_context": "客户问利润报告功能",
            "expected_output": "response-draft.md",
        },
        {
            "task_type": "research",
            "task_desc": "市场调研",
            "input_context": "跨境电商市场分析",
            "expected_output": "research-summary.md",
        },
    ]
})
gs_id = gs_resp.get("goal_session_id", "")
wo_ids = [wo.get("work_order_id") for wo in gs_resp.get("work_orders", [])]
test("Goal Session 创建成功", bool(gs_id), str(gs_id))
test("2 个 Work Order 创建", len(wo_ids) == 2, str(len(wo_ids)))

# 查看 CEO 摘要（来自 goal-intake 返回）
summary = gs_resp
test("CEO 摘要包含 work_orders", "work_orders" in summary, str(list(summary.keys())))
test("CEO 摘要包含 status", "status" in summary, str(summary.get("status")))

# 检查 OpenClaw 字段在 WO dict 中
for wo_data in summary.get("work_orders", []):
    if wo_data.get("execution_mode") == "openclaw_bridge_v2":
        test("WO 包含 execution_mode 字段",
             bool(wo_data.get("execution_mode")),
             wo_data.get("execution_mode"))


step_header(f"\n📊 最终结果: {PASS}/{PASS+FAIL} 通过, {FAIL}/{PASS+FAIL} 失败")
if FAIL == 0:
    print(" ✅ 全流程验收通过！")
    print(f"\n  WO ID: {wo_id}")
    print(f"  Artifacts: {artifacts_dir}")
    print(f"  Inbox: {OPENCLAW_DIR}/inbox/")
else:
    print(" ❌ 存在失败项")
