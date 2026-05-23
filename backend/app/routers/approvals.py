from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime
from app.database import get_sync_session
from app.models.approval import Approval
from app.schemas.approval import ApprovalCreate, ApprovalDecisionRequest, ApprovalResponse

router = APIRouter(tags=["Approvals"])


@router.get("/api/v1/approvals", response_model=list[ApprovalResponse])
def list_approvals(
    status: Optional[str] = Query(None),
    target_type: Optional[str] = Query(None),
):
    session = get_sync_session()
    try:
        query = session.query(Approval)
        if status:
            query = query.filter(Approval.status == status)
        if target_type:
            query = query.filter(Approval.target_type == target_type)

        approvals = query.order_by(Approval.created_at.desc()).all()
        return [_approval_to_response(a) for a in approvals]
    finally:
        session.close()


@router.post("/api/v1/approvals", response_model=ApprovalResponse, status_code=201)
def create_approval(body: ApprovalCreate):
    session = get_sync_session()
    try:
        approval = Approval(
            target_type=body.target_type,
            target_id=body.target_id,
            risk_level=body.risk_level,
            reason=body.reason,
            decision_context=body.decision_context,
            status="approval_requested",
        )
        session.add(approval)
        session.commit()
        session.refresh(approval)
        return _approval_to_response(approval)
    finally:
        session.close()


@router.patch("/api/v1/approvals/{approval_id}/decide", response_model=ApprovalResponse)
def decide_approval(approval_id: int, body: ApprovalDecisionRequest):
    session = get_sync_session()
    try:
        approval = session.query(Approval).filter(Approval.id == approval_id).first()
        if not approval:
            raise HTTPException(status_code=404, detail="Approval not found")

        if approval.status != "approval_requested":
            raise HTTPException(
                status_code=400,
                detail=f"Approval already has status: {approval.status}"
            )

        approval.founder_decision = body.founder_decision
        approval.founder_notes = body.founder_notes

        # Map decision to status
        if body.founder_decision == "approved":
            approval.status = "approved"
            approval.approved_at = datetime.utcnow()
        elif body.founder_decision == "rejected":
            approval.status = "rejected"
        elif body.founder_decision == "deferred":
            approval.status = "expired"
        elif body.founder_decision == "revised":
            approval.status = "approved"
            approval.approved_at = datetime.utcnow()

        session.commit()
        session.refresh(approval)
        return _approval_to_response(approval)
    finally:
        session.close()


def _approval_to_response(a: Approval) -> ApprovalResponse:
    return ApprovalResponse(
        id=a.id,
        target_type=a.target_type,
        target_id=a.target_id,
        risk_level=a.risk_level,
        reason=a.reason,
        founder_decision=a.founder_decision,
        founder_notes=a.founder_notes,
        decision_context=a.decision_context,
        status=a.status,
        approved_at=a.approved_at.isoformat() if a.approved_at else None,
        created_at=a.created_at.isoformat() if a.created_at else None,
    )
