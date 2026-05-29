# @PRODUCT Router — v0.10 CEO Orchestrator API
"""
CEO Orchestrator API — 目标 intake → 自动创建 Work Orders → 路由 → 执行。

端点：
  POST /api/v1/ceo/goal-intake    创建 Goal Session + Work Orders + 自动执行
  GET  /api/v1/ceo/goal-sessions   列出所有 Goal Sessions
  GET  /api/v1/ceo/goal-sessions/{id}  查看 Goal Session 详情 + Work Orders
"""
from fastapi import APIRouter, HTTPException, Query
from app.database import get_sync_session
from app.models.goal_session import GoalSession
from app.models.work_order import WorkOrder
from app.services.ceo_orchestrator import CEOOrchestrator

router = APIRouter(prefix="/api/v1/ceo", tags=["ceo-orchestrator"])


@router.post("/goal-intake")
async def goal_intake(data: dict):
    """
    目标 intake 端点。

    接受 CEO 目标 + 任务列表，自动：
      1. 创建 Goal Session
      2. 为每个 task 创建 Work Order
      3. 批量路由（Skill Router）
      4. 自动执行（WorkOrderExecutor）
      5. 汇总结果写入 Evidence

    Request body:
    ```json
    {
        "goal": "为利润报告产品创建 landing page",
        "product_line_id": "ai-seller-finance",
        "auto_execute": true,
        "tasks": [
            {
                "task_type": "research",
                "task_desc": "研究目标用户痛点",
                "input_context": "...",
                "expected_output": "research summary"
            },
            {
                "task_type": "landing_page_copy",
                "task_desc": "写 landing page 文案",
                "input_context": "...",
                "expected_output": "copy draft"
            }
        ]
    }
    ```

    Returns:
        完整编排结果（含 Goal Session ID、Work Orders、执行结果、汇总）
    """
    goal = data.get("goal", "")
    if not goal:
        raise HTTPException(status_code=400, detail="'goal' is required")

    product_line_id = data.get("product_line_id", "")
    tasks = data.get("tasks", [])
    auto_execute = data.get("auto_execute", True)

    if not tasks:
        raise HTTPException(
            status_code=400,
            detail="'tasks' array is required with at least one task",
        )

    orchestrator = CEOOrchestrator(auto_execute=auto_execute)
    result = orchestrator.run_goal_workflow(
        goal=goal,
        product_line_id=product_line_id,
        tasks=tasks,
        execute=auto_execute,
    )

    return result


@router.get("/goal-sessions")
async def list_goal_sessions(
    limit: int = Query(20, ge=1, le=100),
    status: str = "",
):
    """列出所有 Goal Sessions（按创建时间倒序）"""
    session = get_sync_session()
    try:
        q = session.query(GoalSession).order_by(GoalSession.created_at.desc())
        if status:
            q = q.filter_by(status=status)
        gs_list = q.limit(limit).all()
        return {
            "goal_sessions": [
                {
                    "id": gs.id,
                    "raw_goal": gs.raw_goal,
                    "interpreted_goal": gs.interpreted_goal,
                    "business_line": gs.business_line,
                    "status": gs.status,
                    "task_ids_json": gs.task_ids_json,
                    "priority": gs.priority,
                    "created_at": str(gs.created_at) if gs.created_at else None,
                }
                for gs in gs_list
            ]
        }
    finally:
        session.close()


@router.get("/goal-sessions/{session_id}")
async def get_goal_session(session_id: int):
    """获取 Goal Session 详情及其关联的 Work Orders"""
    session = get_sync_session()
    try:
        gs = session.query(GoalSession).filter_by(id=session_id).first()
        if not gs:
            raise HTTPException(
                status_code=404, detail=f"Goal session #{session_id} not found"
            )

        # Find associated work orders
        work_orders = session.query(WorkOrder).filter_by(
            goal_session_id=str(session_id)
        ).order_by(WorkOrder.created_at.asc()).all()

        return {
            "goal_session": {
                "id": gs.id,
                "raw_goal": gs.raw_goal,
                "interpreted_goal": gs.interpreted_goal,
                "goal_type": gs.goal_type,
                "business_line": gs.business_line,
                "priority": gs.priority,
                "risk_level": gs.risk_level,
                "status": gs.status,
                "decomposition_json": gs.decomposition_json,
                "task_ids_json": gs.task_ids_json,
                "model_used": gs.model_used,
                "confidence": gs.confidence,
                "error_message": gs.error_message,
                "created_at": str(gs.created_at) if gs.created_at else None,
                "updated_at": str(gs.updated_at) if gs.updated_at else None,
            },
            "work_orders": [wo.to_dict() for wo in work_orders],
        }
    finally:
        session.close()
