# @PRODUCT Router — v0.10 Work Orders / v0.13 OpenClaw Callback
import json
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from app.database import get_sync_session
from app.models.work_order import WorkOrder

router = APIRouter(prefix="/api/v1/work-orders", tags=["work-orders"])


def _generate_wo_id() -> str:
    return f"WO-{uuid.uuid4().hex[:8].upper()}"


@router.get("")
async def list_work_orders(
    goal_session_id: str = "",
    product_line_id: str = "",
    status: str = "",
    skill_id: str = "",
):
    """List work orders with optional filters."""
    session = get_sync_session()
    try:
        q = session.query(WorkOrder).order_by(WorkOrder.created_at.desc())
        if goal_session_id:
            q = q.filter_by(goal_session_id=goal_session_id)
        if product_line_id:
            q = q.filter_by(product_line_id=product_line_id)
        if status:
            q = q.filter_by(status=status)
        if skill_id:
            q = q.filter_by(skill_id=skill_id)
        orders = q.all()
        return {"work_orders": [o.to_dict() for o in orders]}
    finally:
        session.close()


@router.get("/{work_order_id}")
async def get_work_order(work_order_id: str):
    session = get_sync_session()
    try:
        wo = session.query(WorkOrder).filter_by(work_order_id=work_order_id).first()
        if not wo:
            raise HTTPException(status_code=404, detail=f"Work order '{work_order_id}' not found")
        return wo.to_dict()
    finally:
        session.close()


@router.post("")
async def create_work_order(data: dict):
    """Create a new work order. Returns the created work order with auto-generated ID."""
    session = get_sync_session()
    try:
        # Store source metadata (draft, brief, decision) in routing_log_json
        source_meta = {}
        for key in ("source_brief", "source_decision", "source_draft"):
            if key in data:
                source_meta[key] = data[key]

        wo = WorkOrder(
            work_order_id=data.get("work_order_id", _generate_wo_id()),
            goal_session_id=data.get("goal_session_id", ""),
            product_line_id=data.get("product_line_id", ""),
            skill_id=data.get("skill_id", ""),
            task_type=data.get("task_type", ""),
            route_reason=data.get("route_reason", ""),
            risk_level=data.get("risk_level", "low"),
            execution_mode=data.get("execution_mode", "direct_delegate"),
            assigned_agent=data.get("assigned_agent", ""),
            runtime_id=data.get("runtime_id", ""),
            input_context=data.get("input_context", ""),
            expected_output=data.get("expected_output", ""),
            approval_required=bool(data.get("approval_required", False)),
            status="created",
            routing_log_json=json.dumps(source_meta) if source_meta else "",
        )
        session.add(wo)
        session.commit()
        return wo.to_dict()
    finally:
        session.close()


@router.patch("/{work_order_id}")
async def update_work_order(work_order_id: str, data: dict):
    """Update work order fields (status, output_path, etc.)."""
    session = get_sync_session()
    try:
        wo = session.query(WorkOrder).filter_by(work_order_id=work_order_id).first()
        if not wo:
            raise HTTPException(status_code=404, detail=f"Work order '{work_order_id}' not found")

        updatable = [
            "status", "goal_session_id", "product_line_id", "skill_id",
            "task_type", "route_reason", "risk_level", "execution_mode",
            "assigned_agent", "runtime_id", "input_context", "expected_output",
            "approval_required", "approval_id", "attempt_count",
            "output_path", "evidence_path", "error", "result_summary",
            "artifacts_json", "routing_log_json", "execution_log_json",
            "approved_for_dispatch_at",
        ]
        for key in updatable:
            if key in data:
                setattr(wo, key, data[key])

        # Auto-set timestamps based on status transitions
        if data.get("status") == "assigned" and not wo.assigned_at:
            wo.assigned_at = datetime.utcnow()
        if data.get("status") in ("completed", "failed", "cancelled") and not wo.completed_at:
            wo.completed_at = datetime.utcnow()

        # v0.21: Convert string datetimes from approve-dispatch command
        if "approved_for_dispatch_at" in data:
            from datetime import datetime as _dt
            val = data["approved_for_dispatch_at"]
            if isinstance(val, str):
                try:
                    wo.approved_for_dispatch_at = _dt.strptime(val, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    wo.approved_for_dispatch_at = _dt.fromisoformat(val)
            else:
                wo.approved_for_dispatch_at = val

        session.commit()
        return wo.to_dict()
    finally:
        session.close()


@router.post("/{work_order_id}/route")
async def route_work_order(work_order_id: str):
    """Route a work order: find matching skill and set status to 'routed'.

    v0.15: Uses YAML-based Skill Registry.
    Unknown task_type → needs_review (not blocked).
    Records skill_id, selected_agent, runtime, risk, approval, routing_reason.
    """
    from app.services.skill_router import route as skill_route

    session = get_sync_session()
    try:
        wo = session.query(WorkOrder).filter_by(work_order_id=work_order_id).first()
        if not wo:
            raise HTTPException(status_code=404, detail=f"Work order '{work_order_id}' not found")

        result = skill_route(wo.task_type)
        if "error" in result:
            # v0.15: unknown task_type → needs_review
            wo.status = "blocked"
            wo.route_reason = result.get("reason", "No matching skill")
            wo.routing_log_json = str(result)
            session.commit()
            return {"status": "needs_review", "reason": result["reason"]}

        wo.status = "routed"
        wo.skill_id = result["skill_id"]
        wo.runtime_id = result["runtime_id"]
        wo.risk_level = result["risk_level"]
        wo.execution_mode = result["execution_mode"]
        wo.assigned_agent = result.get("owner_agent", "")
        wo.route_reason = result.get("routing_reason",
            f"task_type '{wo.task_type}' → skill '{result['skill_id']}'")

        # Approval from registry contract
        wo.approval_required = bool(result.get("approval_required", False))

        wo.routing_log_json = str(result)

        session.commit()
        return wo.to_dict()
    finally:
        session.close()


@router.post("/{work_order_id}/execute")
async def execute_work_order(work_order_id: str):
    """Mark work order as in_progress (actual execution handled by WorkOrderExecutor)."""
    session = get_sync_session()
    try:
        wo = session.query(WorkOrder).filter_by(work_order_id=work_order_id).first()
        if not wo:
            raise HTTPException(status_code=404, detail=f"Work order '{work_order_id}' not found")

        # Safety check: medium/high risk must have approval
        if wo.risk_level in ("medium", "high") and wo.approval_required and not wo.approval_id:
            raise HTTPException(status_code=403, detail="Approval required before execution")

        wo.status = "in_progress"
        wo.attempt_count = (wo.attempt_count or 0) + 1
        session.commit()
        return wo.to_dict()
    finally:
        session.close()


@router.post("/{work_order_id}/complete")
async def complete_work_order(work_order_id: str, data: dict = {}):
    """Mark work order as completed with result paths."""
    session = get_sync_session()
    try:
        wo = session.query(WorkOrder).filter_by(work_order_id=work_order_id).first()
        if not wo:
            raise HTTPException(status_code=404, detail=f"Work order '{work_order_id}' not found")

        wo.status = data.get("status", "completed")
        wo.output_path = data.get("output_path", wo.output_path)
        wo.evidence_path = data.get("evidence_path", wo.evidence_path)
        wo.result_summary = data.get("result_summary", wo.result_summary)
        wo.artifacts_json = data.get("artifacts_json", wo.artifacts_json)
        wo.error = data.get("error", "")
        wo.completed_at = datetime.utcnow()

        session.commit()
        return wo.to_dict()
    finally:
        session.close()


# ── v0.13: OpenClaw Callback Endpoint ──

@router.post("/{work_order_id}/openclaw-callback")
async def openclaw_callback(work_order_id: str, data: dict):
    """
    OpenClaw callback endpoint — receive execution results.

    POST /api/v1/work-orders/{wo_id}/openclaw-callback

    Body:
    ```json
    {
        "status": "completed",
        "result_summary": "...",
        "output_path": "...",
        "artifacts": [{"name": "...", "path": "...", "type": "..."}],
        "confidence": 0.95,
        "api_key": "oc-test-key-change-me",
        "unresolved_questions": ["..."],
        "recommended_follow_up": "...",
        "completed_at": "..."
    }
    ```

    Idempotency:
      - If WO is already 'completed' and same status is sent → OK (no-op)
      - If WO is 'completed' and different status → rejected unless force=true
    """
    from app.services.openclaw_callback import (
        validate_api_key,
        validate_callback_body,
        check_idempotent,
        apply_callback_to_work_order,
    )

    # Get API key from body
    api_key = data.pop("api_key", "")

    session = get_sync_session()
    try:
        wo = session.query(WorkOrder).filter_by(work_order_id=work_order_id).first()
        if not wo:
            raise HTTPException(
                status_code=404,
                detail=f"Work order '{work_order_id}' not found",
            )

        # 1. Validate API key
        if not validate_api_key(api_key):
            raise HTTPException(
                status_code=401,
                detail="Invalid API key. Provide api_key in body.",
            )

        # 2. Validate callback body
        errors = validate_callback_body(data)
        if errors:
            raise HTTPException(
                status_code=400,
                detail={"message": "Invalid callback body", "errors": errors},
            )

        # 3. Check idempotency
        force = data.get("force", False)
        idempotent_error = check_idempotent(
            wo.to_dict(), data.get("status", ""), force=force
        )
        if idempotent_error:
            raise HTTPException(
                status_code=409,
                detail=idempotent_error,
            )

        # 4. Apply callback results
        wo_dict = wo.to_dict()
        applied = apply_callback_to_work_order(wo_dict, data, force=force)
        wo_updates = applied["wo_updates"]
        log_entry = applied["execution_log_entry"]

        # Update work order fields
        for key, value in wo_updates.items():
            setattr(wo, key, value)

        # Update execution_log_json (append)
        existing_log = []
        if wo.execution_log_json:
            try:
                existing_log = json.loads(wo.execution_log_json)
                if not isinstance(existing_log, list):
                    existing_log = [existing_log]
            except (json.JSONDecodeError, TypeError):
                existing_log = []
        existing_log.append(log_entry)
        wo.execution_log_json = json.dumps(existing_log, ensure_ascii=False)

        session.commit()

        return {
            "status": "accepted",
            "work_order": wo.to_dict(),
            "artifacts": applied["artifacts"],
        }
    finally:
        session.close()
