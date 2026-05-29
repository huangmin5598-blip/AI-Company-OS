# @PRODUCT Service — v0.10 CEO Orchestrator
"""
CEO Orchestrator — 目标拆解 → Work Orders → 路由 → 执行 → 汇总。

MVP 实现：
  1. 接受 goal + task list（由 CEO Skill 或 API 调用者提供）
  2. 为每个 task 创建 Work Order
  3. 批量路由（Skill Router）
  4. 批量执行（WorkOrderExecutor）
  5. 收集结果 → 生成汇总 → 写入 Evidence

注意：
  - MVP 不包含 LLM 目标拆解（拆解由 CEO Skill / 用户完成）
  - 执行默认为顺序执行，后续可扩展并行
  - 所有产物写入 artifacts 目录供 CEO Agent 查阅
"""
import json
import os
import time
import uuid
from datetime import datetime
from typing import Optional

from app.database import get_sync_session
from app.models.goal_session import GoalSession
from app.models.work_order import WorkOrder
from app.services.skill_router import route as skill_route, batch_route
from app.services.work_order_executor import execute_work_order


# 默认输出目录
DEFAULT_EVIDENCE_DIR = os.path.expanduser("~/.ai-company-os/evidence/")


def _generate_goal_session_id() -> str:
    return f"GS-{uuid.uuid4().hex[:8].upper()}"


def _ensure_evidence_dir(gs_id: str) -> str:
    path = os.path.join(DEFAULT_EVIDENCE_DIR, gs_id)
    os.makedirs(path, exist_ok=True)
    return path


class CEOOrchestrator:
    """
    CEO Orchestrator — 编排从目标到执行回传的全流程。

    Usage:
        orchestrator = CEOOrchestrator()
        result = orchestrator.run_goal_workflow(
            goal="为利润报告产品创建 landing page",
            product_line_id="ai-seller-finance",
            tasks=[
                {"task_type": "research", "task_desc": "研究目标用户痛点",
                 "input_context": "...", "expected_output": "..."},
                {"task_type": "landing_page_copy", "task_desc": "写落地页文案",
                 "input_context": "...", "expected_output": "..."},
                {"task_type": "landing_page_code", "task_desc": "生成 landing page 代码",
                 "input_context": "...", "expected_output": "..."},
            ]
        )
    """

    def __init__(self, auto_execute: bool = True):
        self.auto_execute = auto_execute

    def run_goal_workflow(
        self,
        goal: str,
        product_line_id: str = "",
        tasks: list[dict] = None,
        goal_session_id: str = "",
        execute: bool = True,
    ) -> dict:
        """
        全流程：创建 Goal Session → 创建 Work Orders → 路由 → 执行 → 汇总

        Args:
            goal: 目标描述
            product_line_id: 所属产品线
            tasks: 任务列表 [{task_type, task_desc, input_context, expected_output}, ...]
            goal_session_id: 可选，已有 Goal Session ID
            execute: 是否自动执行（默认 True）

        Returns:
            {
                "goal_session_id": str,
                "goal": str,
                "work_orders": [WorkOrder dicts],
                "execution_results": [Execution results],
                "summary": str,
                "evidence_dir": str,
                "status": "completed" / "partial" / "failed",
            }
        """
        gs_id = goal_session_id or _generate_goal_session_id()
        evidence_dir = _ensure_evidence_dir(gs_id)
        session = get_sync_session()

        try:
            # 1. Create or update Goal Session
            existing_gs = session.query(GoalSession).filter_by(
                id=gs_id if gs_id.isdigit() else 0
            ).first()

            if not existing_gs and not goal_session_id:
                # Create new goal session
                gs = GoalSession(
                    raw_goal=goal,
                    interpreted_goal=goal,
                    business_line=product_line_id,
                    status="decomposed",
                )
                session.add(gs)
                session.commit()
                gs_id_val = str(gs.id)
            else:
                gs_id_val = gs_id

            if not tasks:
                return {
                    "goal_session_id": gs_id_val,
                    "goal": goal,
                    "work_orders": [],
                    "execution_results": [],
                    "summary": "No tasks provided — CEO Orchestrator requires at least one task",
                    "evidence_dir": evidence_dir,
                    "status": "failed",
                }

            # 2. Batch route tasks
            routing_results = batch_route(tasks)

            # 3. Create Work Orders
            wo_ids = []
            work_orders = []
            for i, task in enumerate(tasks):
                route_info = routing_results[i] if i < len(routing_results) else {}

                wo = WorkOrder(
                    work_order_id=f"WO-{uuid.uuid4().hex[:8].upper()}",
                    goal_session_id=gs_id_val,
                    product_line_id=product_line_id,
                    skill_id=route_info.get("skill_id", ""),
                    task_type=task.get("task_type", ""),
                    route_reason=route_info.get("route_reason", f"Task #{i+1}: {task.get('task_desc', '')}"),
                    risk_level=route_info.get("risk_level", "low"),
                    execution_mode=route_info.get("execution_mode", "direct_delegate"),
                    assigned_agent=route_info.get("owner_agent", ""),
                    runtime_id=route_info.get("runtime_id", ""),
                    input_context=task.get("input_context", ""),
                    expected_output=task.get("expected_output", ""),
                    status="created",
                )
                session.add(wo)
                session.flush()

                # If routed successfully, update with routing info
                if "error" not in route_info:
                    wo.status = "routed"
                    wo.routing_log_json = json.dumps(route_info, ensure_ascii=False)

                wo_ids.append(wo.work_order_id)
                work_orders.append(wo.to_dict())

            session.commit()

            # Save goal session task IDs
            task_ids_json = json.dumps(wo_ids, ensure_ascii=False)
            if not existing_gs:
                gs = session.query(GoalSession).order_by(
                    GoalSession.id.desc()
                ).first()
                if gs:
                    gs.task_ids_json = task_ids_json
                    session.commit()

            # 4. Execute (if requested)
            execution_results = []
            if execute:
                for wo_id in wo_ids:
                    exec_result = execute_work_order(wo_id)
                    execution_results.append(exec_result)

            # 5. Generate summary
            summary_parts = []
            completed_count = 0
            failed_count = 0
            pending_count = 0

            if execution_results:
                for r in execution_results:
                    wo = r.get("work_order", {})
                    er = r.get("execution_result", {})
                    wo_status = wo.get("status", "unknown")
                    task_type = wo.get("task_type", "")

                    if wo_status == "completed":
                        completed_count += 1
                    elif wo_status in ("failed",):
                        failed_count += 1
                    else:
                        pending_count += 1

                    summary_parts.append(
                        f"- `{task_type}` → **{wo_status}**: {er.get('summary', 'No summary')}"
                    )
            else:
                for wo in work_orders:
                    summary_parts.append(
                        f"- `{wo.get('task_type', '')}` → **created** (not executed)"
                    )
                pending_count = len(work_orders)

            summary_lines = [
                f"## CEO Orchestration Summary",
                f"",
                f"**Goal:** {goal}",
                f"**Session:** `{gs_id_val}`",
                f"**Product Line:** {product_line_id or 'N/A'}",
                f"**Tasks:** {len(tasks)} total | ✅ {completed_count} completed | ❌ {failed_count} failed | ⏳ {pending_count} pending",
                f"",
                f"### Execution Details",
            ] + summary_parts

            summary = "\n".join(summary_lines)

            # Write summary to evidence_dir
            summary_path = os.path.join(evidence_dir, "ceo_summary.md")
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(summary)

            overall_status = (
                "completed" if completed_count == len(tasks) and failed_count == 0
                else "partial" if completed_count > 0 or pending_count > 0
                else "failed"
            )

            return {
                "goal_session_id": gs_id_val,
                "goal": goal,
                "work_orders": work_orders,
                "execution_results": execution_results,
                "summary": summary,
                "summary_path": summary_path,
                "evidence_dir": evidence_dir,
                "status": overall_status,
                "stats": {
                    "total": len(tasks),
                    "completed": completed_count,
                    "failed": failed_count,
                    "pending": pending_count,
                },
            }

        except Exception as e:
            return {
                "goal_session_id": goal_session_id or "",
                "goal": goal,
                "work_orders": [],
                "execution_results": [],
                "summary": f"CEO Orchestrator failed: {str(e)}",
                "evidence_dir": evidence_dir,
                "status": "failed",
                "error": str(e),
            }
        finally:
            session.close()

    def run_from_goal_session(self, goal_session_id: str, execute: bool = True) -> dict:
        """
        从已有的 Goal Session 重新运行。
        MVP: 简化版 — 查找该 session 关联的 Work Orders 并执行。
        """
        session = get_sync_session()
        try:
            work_orders = session.query(WorkOrder).filter_by(
                goal_session_id=goal_session_id
            ).all()

            wo_ids = [wo.work_order_id for wo in work_orders]
            execution_results = []
            if execute and wo_ids:
                for wo_id in wo_ids:
                    result = execute_work_order(wo_id)
                    execution_results.append(result)

            return {
                "goal_session_id": goal_session_id,
                "work_orders": [wo.to_dict() for wo in work_orders],
                "execution_results": execution_results,
                "status": "ok",
            }
        finally:
            session.close()
