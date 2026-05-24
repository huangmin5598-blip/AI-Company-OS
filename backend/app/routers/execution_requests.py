# @PRODUCT Router — OS Core
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.database import get_sync_session
from app.models.execution_request import ExecutionRequest

router = APIRouter(prefix="/api/v1/execution-requests", tags=["execution"])


# ── Schemas ──


class ConfirmRequest(BaseModel):
    confirmed_by: str = "founder"
    note: str = ""


# ── Serializer ──


def serialize(er: ExecutionRequest) -> dict:
    return {
        "id": er.id,
        "source_type": er.source_type,
        "source_id": er.source_id,
        "proposal_id": er.proposal_id,
        "task_id": er.task_id,
        "runtime_id": er.runtime_id,
        "action_type": er.action_type,
        "action_payload": json.loads(er.action_payload_json) if er.action_payload_json else {},
        "risk_level": er.risk_level,
        "dry_run_required": bool(er.dry_run_required),
        "dry_run_result": json.loads(er.dry_run_result_json) if er.dry_run_result_json else None,
        "status": er.status,
        "execute_confirmed_by": er.execute_confirmed_by,
        "execute_confirmed_at": er.execute_confirmed_at.isoformat() if er.execute_confirmed_at else None,
        "execute_confirmation_note": er.execute_confirmation_note,
        "executed_at": er.executed_at.isoformat() if er.executed_at else None,
        "execution_result": json.loads(er.execution_result_json) if er.execution_result_json else None,
        "verification_result": json.loads(er.verification_result_json) if er.verification_result_json else None,
        "verified_by": er.verified_by,
        "verified_at": er.verified_at.isoformat() if er.verified_at else None,
        "created_at": er.created_at.isoformat() if er.created_at else None,
        "updated_at": er.updated_at.isoformat() if er.updated_at else None,
    }


# ── Endpoints ──


@router.get("")
def list_requests(
    status: str = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    session = get_sync_session()
    try:
        q = session.query(ExecutionRequest).order_by(ExecutionRequest.created_at.desc())
        if status:
            q = q.filter(ExecutionRequest.status == status)
        return [serialize(r) for r in q.offset(offset).limit(limit).all()]
    finally:
        session.close()


@router.get("/{request_id}")
def get_request(request_id: int):
    session = get_sync_session()
    try:
        er = session.query(ExecutionRequest).filter_by(id=request_id).first()
        if not er:
            raise HTTPException(404, "Execution request not found")
        return serialize(er)
    finally:
        session.close()


@router.post("/{request_id}/dry-run")
async def dry_run_request(request_id: int):
    """Run dry-run for a command-type execution request.

    Dry-run generates text preview only — no shell execution.
    Status must be pending_confirmation and dry_run_required=true.
    """
    from app.execution_bridge.policy import validate_transition
    from app.execution_bridge.dry_run import run_dry_run

    session = get_sync_session()
    try:
        er = session.query(ExecutionRequest).filter_by(id=request_id).first()
        if not er:
            raise HTTPException(404, "Execution request not found")
        if not er.dry_run_required:
            raise HTTPException(400, "This action type does not require dry-run")

        tx = validate_transition(er.status, "dry_run")
        if not tx["allowed"]:
            raise HTTPException(400, tx["reason"])

        result = await run_dry_run(request_id)
        return result
    finally:
        session.close()


@router.post("/{request_id}/confirm")
def confirm_execution(request_id: int, req: ConfirmRequest = ConfirmRequest()):
    """Founder confirms execution. Transitions to approved_for_execute.

    For command-type actions (dry_run_required=true), dry-run must be completed first.
    Records execute_confirmed_by / execute_confirmed_at for audit.
    """
    from app.execution_bridge.policy import validate_transition

    session = get_sync_session()
    try:
        er = session.query(ExecutionRequest).filter_by(id=request_id).first()
        if not er:
            raise HTTPException(404, "Execution request not found")

        # Command-type actions must dry-run first
        if er.dry_run_required and er.status != "dry_run_completed":
            raise HTTPException(
                400,
                f"Action requires dry-run first. Status is '{er.status}', expected 'dry_run_completed'",
            )

        tx = validate_transition(er.status, "confirm")
        if not tx["allowed"]:
            raise HTTPException(400, tx["reason"])

        er.status = tx["to"]
        er.execute_confirmed_by = req.confirmed_by
        er.execute_confirmed_at = datetime.utcnow()
        er.execute_confirmation_note = req.note
        session.commit()

        return {"request_id": er.id, "status": er.status, "confirmed_by": req.confirmed_by}
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.post("/{request_id}/execute")
async def execute_request(request_id: int):
    """Execute a confirmed safe action. One-shot — no retry.

    Status must be approved_for_execute.
    verified_success/verified_failed cannot be re-executed.
    """
    from app.execution_bridge.policy import validate_transition
    from app.execution_bridge.executor import execute_safe_action

    session = get_sync_session()
    try:
        er = session.query(ExecutionRequest).filter_by(id=request_id).first()
        if not er:
            raise HTTPException(404, "Execution request not found")

        tx = validate_transition(er.status, "execute")
        if not tx["allowed"]:
            raise HTTPException(400, tx["reason"])

        result = await execute_safe_action(request_id)
        return {"request_id": er.id, "status": "executed", "result": result}
    except ValueError as e:
        raise HTTPException(400, str(e))
    finally:
        session.close()


@router.post("/{request_id}/verify")
async def verify_request(request_id: int):
    """Run verification for an executed action.

    Status must be executed.
    Writes verification_result and syncs proposal status.
    """
    from app.execution_bridge.policy import validate_transition
    from app.execution_bridge.verification import run_verification

    session = get_sync_session()
    try:
        er = session.query(ExecutionRequest).filter_by(id=request_id).first()
        if not er:
            raise HTTPException(404, "Execution request not found")

        tx = validate_transition(er.status, "verify")
        if not tx["allowed"]:
            raise HTTPException(400, tx["reason"])

        result = await run_verification(request_id)
        return {
            "request_id": er.id,
            "status": "verified_success" if result.get("verified") else "verified_failed",
            "result": result,
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
    finally:
        session.close()


@router.post("/{request_id}/cancel")
def cancel_request(request_id: int):
    """Cancel a pending execution request."""
    from app.execution_bridge.policy import validate_transition

    session = get_sync_session()
    try:
        er = session.query(ExecutionRequest).filter_by(id=request_id).first()
        if not er:
            raise HTTPException(404, "Execution request not found")

        tx = validate_transition(er.status, "cancel")
        if not tx["allowed"]:
            raise HTTPException(400, tx["reason"])

        er.status = tx["to"]
        session.commit()

        return {"request_id": er.id, "status": er.status}
    finally:
        session.close()
