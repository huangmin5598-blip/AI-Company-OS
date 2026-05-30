# @PRODUCT Service — v0.10 Work Order Executor
"""
Work Order Executor — 根据 execution_mode 分派执行并回填结果。

执行矩阵：
| execution_mode       | 方法                           | 实现                     |
|:---------------------|:-------------------------------|:-------------------------|
| direct_delegate      | 返回执行指令（Hermes 执行）     | mock_hermes_delegate     |
| code_bridge          | 生成 Code Bridge 请求          | execute_code_bridge      |
| local_script         | subprocess.run()               | execute_local_script     |
| openclaw_task_card   | OpenClawBridge task card       | execute_openclaw         |
| checklist_only       | 生成安全检查清单                | execute_checklist        |
| manual               | 标记为需要人工介入              | execute_manual           |

回填逻辑：
  执行完成 → PATCH Work Order
    → status = completed / failed
    → output_path = 产物路径
    → evidence_path = 证据路径
    → result_summary = 执行摘要
    → completed_at = now
"""
import json
import os
import subprocess
import time
import uuid
from datetime import datetime
from typing import Optional

from app.database import get_sync_session
from app.models.work_order import WorkOrder


# 本地脚本映射：skill_id → 可执行脚本路径
LOCAL_SCRIPT_MAP = {
    "profit_health_report_generator": os.path.expanduser(
        "~/Documents/Codex/ai-company-os/projects/ai-seller-finance-validation/scripts/generate_profit_health_report.py"
    ),
}

# 默认产物输出目录
DEFAULT_ARTIFACTS_DIR = os.path.expanduser("~/.ai-company-os/artifacts/")


def _generate_execution_id() -> str:
    return f"EXEC-{uuid.uuid4().hex[:8].upper()}"


def _ensure_artifacts_dir(wo_id: str) -> str:
    """Create per-work-order artifact directory and return path."""
    path = os.path.join(DEFAULT_ARTIFACTS_DIR, wo_id)
    os.makedirs(path, exist_ok=True)
    return path


def _save_execution_log(wo_id: str, log_entry: dict) -> str:
    """Append execution log entry to JSON file."""
    log_dir = os.path.join(DEFAULT_ARTIFACTS_DIR, wo_id)
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "execution_log.json")
    entries = []
    if os.path.exists(log_path):
        try:
            entries = json.loads(open(log_path, encoding="utf-8").read())
        except (json.JSONDecodeError, OSError):
            entries = []
    entries.append(log_entry)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    return log_path


def _update_work_order(
    wo_id: str, updates: dict, session=None
) -> Optional[dict]:
    """Update a work order in the database. Manages its own session if not provided."""
    close_session = False
    if session is None:
        session = get_sync_session()
        close_session = True
    try:
        wo = session.query(WorkOrder).filter_by(work_order_id=wo_id).first()
        if not wo:
            return None

        for key, value in updates.items():
            setattr(wo, key, value)

        # Auto-set timestamps
        if updates.get("status") == "in_progress":
            wo.attempt_count = (wo.attempt_count or 0) + 1
        if updates.get("status") in ("completed", "failed", "cancelled"):
            wo.completed_at = datetime.utcnow()

        session.commit()
        return wo.to_dict()
    finally:
        if close_session:
            session.close()


# ---- Execution Handlers ----


def _mock_hermes_delegate(work_order: dict) -> dict:
    """
    为 direct_delegate 模式生成执行指令。
    实际执行由 Hermes CEO Agent 通过 delegate_task 完成。
    """
    exec_id = _generate_execution_id()
    artifacts_dir = _ensure_artifacts_dir(work_order["work_order_id"])

    # 生成执行指令 JSON
    instruction = {
        "execution_id": exec_id,
        "work_order_id": work_order["work_order_id"],
        "method": "hermes_delegate_task",
        "skill_id": work_order.get("skill_id", ""),
        "task_type": work_order.get("task_type", ""),
        "input_context": work_order.get("input_context", ""),
        "expected_output": work_order.get("expected_output", ""),
        "risk_level": work_order.get("risk_level", "low"),
        "execution_mode": work_order.get("execution_mode", ""),
        "created_at": str(time.time()),
    }

    instruction_path = os.path.join(artifacts_dir, "delegate_instruction.json")
    with open(instruction_path, "w", encoding="utf-8") as f:
        json.dump(instruction, f, ensure_ascii=False, indent=2)

    return {
        "status": "ready_for_delegation",
        "execution_id": exec_id,
        "instruction_path": instruction_path,
        "summary": f"Ready for Hermes delegate_task: {work_order['skill_id']} — {work_order.get('task_type', '')}",
        "execution_log_entry": {
            "event": "delegate_instruction_created",
            "execution_id": exec_id,
            "timestamp": str(time.time()),
        },
    }


def _execute_code_bridge(work_order: dict) -> dict:
    """
    为 code_bridge 模式生成 Code Change Request。
    实际由 Code Bridge 审批/执行流程完成。
    """
    exec_id = _generate_execution_id()
    artifacts_dir = _ensure_artifacts_dir(work_order["work_order_id"])

    ccr = {
        "work_order_id": work_order["work_order_id"],
        "execution_id": exec_id,
        "source": "ceo-orchestrator",
        "skill_id": work_order.get("skill_id", ""),
        "task_type": work_order.get("task_type", ""),
        "context": work_order.get("input_context", ""),
        "expected_output": work_order.get("expected_output", ""),
        "status": "pending",
        "created_at": str(time.time()),
    }

    ccr_path = os.path.join(artifacts_dir, "code_change_request.json")
    with open(ccr_path, "w", encoding="utf-8") as f:
        json.dump(ccr, f, ensure_ascii=False, indent=2)

    return {
        "status": "code_bridge_pending",
        "execution_id": exec_id,
        "ccr_path": ccr_path,
        "summary": f"Code Bridge request generated: {work_order['skill_id']} — {work_order.get('task_type', '')}",
        "approval_required": True,
        "execution_log_entry": {
            "event": "code_bridge_request_created",
            "execution_id": exec_id,
            "ccr_path": ccr_path,
            "timestamp": str(time.time()),
        },
    }


def _execute_local_script(work_order: dict) -> dict:
    """
    为 local_script 模式执行本地脚本。
    查找 LOCAL_SCRIPT_MAP，找不到则尝试从 input_context 提取命令。
    """
    exec_id = _generate_execution_id()
    artifacts_dir = _ensure_artifacts_dir(work_order["work_order_id"])
    skill_id = work_order.get("skill_id", "")

    script_path = LOCAL_SCRIPT_MAP.get(skill_id)

    if not script_path:
        return {
            "status": "failed",
            "execution_id": exec_id,
            "error": f"No local script mapped for skill '{skill_id}'",
            "summary": f"No local script found for {skill_id}",
            "execution_log_entry": {
                "event": "local_script_failed",
                "error": f"Unknown skill: {skill_id}",
                "timestamp": str(time.time()),
            },
        }

    if not os.path.exists(script_path):
        return {
            "status": "failed",
            "execution_id": exec_id,
            "error": f"Script not found: {script_path}",
            "summary": f"Script missing for {skill_id}",
            "execution_log_entry": {
                "event": "local_script_failed",
                "error": f"Script not found: {script_path}",
                "timestamp": str(time.time()),
            },
        }

    try:
        output_path = os.path.join(artifacts_dir, "output.txt")
        evidence_path = os.path.join(artifacts_dir, "evidence.json")

        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=os.path.dirname(script_path),
        )

        # Save output
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.stdout)
            if result.stderr:
                f.write("\n--- STDERR ---\n")
                f.write(result.stderr)

        evidence = {
            "exit_code": result.returncode,
            "stdout_truncated": len(result.stdout),
            "stderr": (
                result.stderr[:500] if result.stderr else ""
            ),
            "completed_at": str(time.time()),
        }
        with open(evidence_path, "w", encoding="utf-8") as f:
            json.dump(evidence, f, ensure_ascii=False, indent=2)

        if result.returncode == 0:
            return {
                "status": "completed",
                "execution_id": exec_id,
                "output_path": output_path,
                "evidence_path": evidence_path,
                "summary": f"Local script completed: {skill_id} (exit code: 0)",
                "execution_log_entry": {
                    "event": "local_script_completed",
                    "script_path": script_path,
                    "exit_code": 0,
                    "timestamp": str(time.time()),
                },
            }
        else:
            return {
                "status": "failed",
                "execution_id": exec_id,
                "output_path": output_path,
                "evidence_path": evidence_path,
                "error": f"Script failed with exit code {result.returncode}",
                "summary": f"Local script failed: {skill_id} (exit code: {result.returncode})",
                "execution_log_entry": {
                    "event": "local_script_failed",
                    "script_path": script_path,
                    "exit_code": result.returncode,
                    "error": result.stderr[:500],
                    "timestamp": str(time.time()),
                },
            }
    except subprocess.TimeoutExpired:
        return {
            "status": "failed",
            "execution_id": exec_id,
            "error": "Script timed out after 120s",
            "summary": f"Local script timed out: {skill_id}",
            "execution_log_entry": {
                "event": "local_script_timed_out",
                "script_path": script_path,
                "timestamp": str(time.time()),
            },
        }
    except Exception as e:
        return {
            "status": "failed",
            "execution_id": exec_id,
            "error": str(e),
            "summary": f"Local script error: {skill_id} — {str(e)[:200]}",
            "execution_log_entry": {
                "event": "local_script_error",
                "script_path": script_path,
                "error": str(e)[:500],
                "timestamp": str(time.time()),
            },
        }


def _execute_openclaw(work_order: dict) -> dict:
    """
    为 openclaw_task_card 模式创建 OpenClaw task card。
    使用 OpenClawBridge 生成 card 并轮询结果。
    """
    from app.services.openclaw_bridge import OpenClawBridge

    bridge = OpenClawBridge()
    card_result = bridge.create_task_card(work_order)

    if card_result.get("fallback"):
        # 降级：只生成 card 不发送
        return {
            "status": "card_generated",
            "execution_id": _generate_execution_id(),
            "summary": "Task card generated (OpenClaw unavailable — review and submit manually)",
            "card_result": card_result,
            "execution_log_entry": {
                "event": "openclaw_card_created_fallback",
                "card_id": card_result.get("card_id", ""),
                "timestamp": str(time.time()),
            },
        }

    return {
        "status": "pending_openclaw",
        "execution_id": _generate_execution_id(),
        "card_path": card_result.get("card_path", ""),
        "card_id": card_result.get("card_id", ""),
        "summary": f"Task card submitted to OpenClaw: {card_result.get('card_id', '')}",
        "execution_log_entry": {
            "event": "openclaw_card_created",
            "card_id": card_result.get("card_id", ""),
            "card_path": card_result.get("card_path", ""),
            "timestamp": str(time.time()),
        },
    }


def _execute_openclaw_v2(work_order: dict) -> dict:
    """
    为 openclaw_bridge_v2 模式创建增强版 task card 并写入 inbox。
    使用 v0.13 增强的 OpenClawBridge (Inbox/Outbox + Result Manifest)。

    返回状态：
      - openclaw_dispatched: task card 成功写入 inbox
      - card_generated (fallback): 目录不可写，降级
      - failed: 写入失败
    """
    from app.services.openclaw_bridge import OpenClawBridge

    bridge = OpenClawBridge()
    card_result = bridge.create_task_card(work_order)

    exec_id = _generate_execution_id()

    if card_result.get("fallback"):
        return {
            "status": "card_generated",
            "execution_id": exec_id,
            "summary": "Task card generated (OpenClaw unavailable — directory not writable)",
            "card_result": card_result,
            "execution_log_entry": {
                "event": "openclaw_v2_card_fallback",
                "card_id": card_result.get("card_id", ""),
                "reason": "directory_not_writable",
                "timestamp": str(time.time()),
            },
        }

    if card_result.get("status") == "failed":
        return {
            "status": "failed",
            "execution_id": exec_id,
            "error": card_result.get("error", "Unknown error creating task card"),
            "summary": "Failed to dispatch task to OpenClaw",
            "execution_log_entry": {
                "event": "openclaw_v2_card_failed",
                "error": card_result.get("error", ""),
                "timestamp": str(time.time()),
            },
        }

    # Successfully dispatched
    execution_state = card_result.get("execution_state", {})
    inbox_path = card_result.get("inbox_path", "")
    card_path = card_result.get("card_path", "")

    return {
        "status": "openclaw_dispatched",
        "execution_id": exec_id,
        "card_id": card_result.get("card_id", ""),
        "card_path": card_path,
        "inbox_path": inbox_path,
        "execution_state": execution_state,
        "summary": f"Task card dispatched to OpenClaw inbox: {card_result.get('card_id', '')}",
        "execution_log_entry": {
            "event": "openclaw_v2_card_dispatched",
            "card_id": card_result.get("card_id", ""),
            "card_path": card_path,
            "execution_state": execution_state,
            "timestamp": str(time.time()),
        },
    }


def _execute_checklist(work_order: dict) -> dict:
    """
    为 checklist_only 模式生成部署安全检查清单。
    """
    exec_id = _generate_execution_id()
    artifacts_dir = _ensure_artifacts_dir(work_order["work_order_id"])

    checklist = {
        "work_order_id": work_order["work_order_id"],
        "execution_id": exec_id,
        "skill_id": work_order.get("skill_id", ""),
        "task_type": work_order.get("task_type", ""),
        "risk_level": "high",
        "checks": [
            {
                "id": "check-1",
                "description": "确认所有环境变量已配置",
                "status": "pending",
            },
            {
                "id": "check-2",
                "description": "确认域名 DNS 指向正确",
                "status": "pending",
            },
            {
                "id": "check-3",
                "description": "确认 HTTPS 证书已签发",
                "status": "pending",
            },
            {
                "id": "check-4",
                "description": "确认生产数据库备份完成",
                "status": "pending",
            },
            {
                "id": "check-5",
                "description": "确认部署平台 API Token 有效",
                "status": "pending",
            },
            {
                "id": "check-6",
                "description": "确认回滚方案就绪",
                "status": "pending",
            },
            {
                "id": "check-7",
                "description": "确认监控告警已配置",
                "status": "pending",
            },
            {
                "id": "check-8",
                "description": "确认部署通知已发送给团队",
                "status": "pending",
            },
        ],
        "created_at": str(time.time()),
        "instructions": "请逐项确认后，PATCH /api/v1/work-orders/{id}/complete 回填结果",
    }

    checklist_path = os.path.join(artifacts_dir, "deploy_checklist.json")
    with open(checklist_path, "w", encoding="utf-8") as f:
        json.dump(checklist, f, ensure_ascii=False, indent=2)

    return {
        "status": "checklist_ready",
        "execution_id": exec_id,
        "checklist_path": checklist_path,
        "summary": f"Deploy checklist generated: {len(checklist['checks'])} checks — manual review required",
        "execution_log_entry": {
            "event": "checklist_generated",
            "checklist_path": checklist_path,
            "check_count": len(checklist["checks"]),
            "timestamp": str(time.time()),
        },
    }


def _execute_manual(work_order: dict) -> dict:
    """
    为 manual 模式标记为需要人工介入。
    """
    exec_id = _generate_execution_id()
    artifacts_dir = _ensure_artifacts_dir(work_order["work_order_id"])

    manual_ticket = {
        "work_order_id": work_order["work_order_id"],
        "execution_id": exec_id,
        "reason": "This task requires manual execution (execution_mode=manual)",
        "context": work_order.get("input_context", ""),
        "expected_output": work_order.get("expected_output", ""),
        "created_at": str(time.time()),
        "instructions": "Please complete manually and PATCH /api/v1/work-orders/{id}/complete",
    }

    ticket_path = os.path.join(artifacts_dir, "manual_ticket.json")
    with open(ticket_path, "w", encoding="utf-8") as f:
        json.dump(manual_ticket, f, ensure_ascii=False, indent=2)

    return {
        "status": "manual_required",
        "execution_id": exec_id,
        "ticket_path": ticket_path,
        "summary": f"Manual execution required: {work_order.get('task_type', '')}",
        "execution_log_entry": {
            "event": "manual_ticket_created",
            "timestamp": str(time.time()),
        },
    }


# ---- Execution Mode Dispatch Map ----

EXECUTION_HANDLERS = {
    "direct_delegate": _mock_hermes_delegate,
    "code_bridge": _execute_code_bridge,
    "local_script": _execute_local_script,
    "openclaw_task_card": _execute_openclaw,
    "openclaw_bridge_v2": _execute_openclaw_v2,
    "openclaw_agent": _execute_openclaw_v2,       # v0.15 YAML registry compat
    "checklist_only": _execute_checklist,
    "manual": _execute_manual,
}


# ---- Public Interface ----


def execute_work_order(work_order_id: str) -> dict:
    """
    执行一个 Work Order。

    流程：
      1. 读取 Work Order 记录
      2. 根据 execution_mode 选择处理方法
      3. 执行
      4. 回填结果到数据库

    Args:
        work_order_id: Work Order ID

    Returns:
        执行结果 dict（含回填后的 Work Order 快照）
    """
    session = get_sync_session()
    try:
        # 1. Load work order
        wo = session.query(WorkOrder).filter_by(
            work_order_id=work_order_id
        ).first()
        if not wo:
            return {"error": f"Work order '{work_order_id}' not found"}

        wo_dict = wo.to_dict()

        # 2. Validate state
        if wo.status != "routed":
            return {
                "error": f"Work order must be 'routed' to execute (current: {wo.status})",
                "work_order": wo_dict,
            }

        # Check approval for medium/high risk
        if wo.risk_level in ("medium", "high") and wo.approval_required and not wo.approval_id:
            return {
                "error": "Approval required before execution",
                "status": "requires_approval",
                "work_order": wo_dict,
            }

        # 3. Mark as in_progress
        wo.status = "in_progress"
        wo.attempt_count = (wo.attempt_count or 0) + 1
        session.commit()

        # 4. Dispatch
        execution_mode = wo.execution_mode or "direct_delegate"
        handler = EXECUTION_HANDLERS.get(execution_mode)
        if not handler:
            wo.status = "failed"
            wo.error = f"Unknown execution_mode: {execution_mode}"
            session.commit()
            return {
                "error": wo.error,
                "work_order": wo.to_dict(),
            }

        try:
            execution_result = handler(wo_dict)
        except Exception as e:
            wo.status = "failed"
            wo.error = f"Handler error: {str(e)}"
            session.commit()
            return {
                "error": wo.error,
                "work_order": wo.to_dict(),
            }

        # 5. Backfill results
        final_status = execution_result.get("status", "failed")

        # Map execution statuses to work order status
        STATUS_MAP = {
            "completed": "completed",
            "ready_for_delegation": "assigned",
            "code_bridge_pending": "requires_approval",
            "pending_openclaw": "in_progress",
            "openclaw_dispatched": "in_progress",
            "checklist_ready": "in_progress",
            "manual_required": "blocked",
            "card_generated": "in_progress",
            "failed": "failed",
        }
        wo.status = STATUS_MAP.get(final_status, "failed")

        # Don't mark delegation-returning statuses as fully completed
        if final_status in ("ready_for_delegation", "code_bridge_pending", "pending_openclaw", "openclaw_dispatched", "checklist_ready", "card_generated"):
            # These still need further processing — don't set completed_at
            pass
        elif final_status == "completed":
            wo.completed_at = datetime.utcnow()

        wo.output_path = execution_result.get("output_path", "")
        wo.evidence_path = execution_result.get("evidence_path", "")
        wo.result_summary = execution_result.get("summary", "")
        wo.error = execution_result.get("error", "")

        # Save execution log
        log_entry = execution_result.get("execution_log_entry", {})
        log_path = _save_execution_log(wo.work_order_id, log_entry)
        wo.execution_log_json = json.dumps(
            [log_entry], ensure_ascii=False
        )

        session.commit()

        return {
            "work_order": wo.to_dict(),
            "execution_result": execution_result,
        }

    finally:
        session.close()


def batch_execute(work_order_ids: list[str]) -> list[dict]:
    """
    批量执行 Work Orders。
    按顺序执行，每个结果包含原始 work_order 快照和执行结果。
    """
    results = []
    for wo_id in work_order_ids:
        result = execute_work_order(wo_id)
        results.append(result)
    return results
