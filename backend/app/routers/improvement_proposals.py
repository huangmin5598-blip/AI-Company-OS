# @PRODUCT Router — OS Core
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.database import get_sync_session
from app.models.improvement_proposal import ImprovementProposal
from app.models.approval import Approval
from app.models.task_pool import TaskPool

router = APIRouter(prefix="/api/v1/improvement-proposals", tags=["improvement"])


# ── Schemas ──


class GenerateRequest(BaseModel):
    finding: dict
    config: dict = {}


class ApproveRequest(BaseModel):
    founder_notes: str = ""
    decision_context: str = ""


class ProposalRejectRequest(BaseModel):
    founder_notes: str = ""


class ProposalCloseRequest(BaseModel):
    result: str  # "success" or "failed"
    verification_result: dict = {}
    verified_by: str = "founder"


# ── Serializer ──


def serialize(p: ImprovementProposal) -> dict:
    return {
        "id": p.id,
        "source_finding_id": p.source_finding_id,
        "source_finding_type": p.source_finding_type,
        "proposal_type": p.proposal_type,
        "title": p.title,
        "summary": p.summary,
        "rationale": p.rationale,
        "action_plan": json.loads(p.action_plan_json) if p.action_plan_json else {},
        "risk_level": p.risk_level,
        "business_line": p.business_line,
        "requires_command_center": bool(p.requires_command_center),
        "recommended_next_step": p.recommended_next_step,
        "status": p.status,
        "approval_id": p.approval_id,
        "created_task_id": p.created_task_id,
        "verification_plan": json.loads(p.verification_plan_json) if p.verification_plan_json else {},
        "verification_result": json.loads(p.verification_result_json) if p.verification_result_json else None,
        "verified_by": p.verified_by,
        "verified_at": p.verified_at.isoformat() if p.verified_at else None,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


# ── Endpoints ──


@router.post("/generate")
def generate_endpoint(req: GenerateRequest):
    """Generate an ImprovementProposal from a monitor finding.

    Config filter: min_severity, auto_generate_for control which findings get proposals.
    Dedup: same source_finding_id + proposal_type → only one active proposal.
    """
    from app.improvement.generator import generate_proposal as gen

    result = gen(req.finding, req.config)
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Proposal generation skipped (dedup, config filter, or unknown finding type)",
        )
    return result


@router.get("")
def list_proposals(
    status: str = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    session = get_sync_session()
    try:
        q = session.query(ImprovementProposal).order_by(ImprovementProposal.created_at.desc())
        if status:
            q = q.filter(ImprovementProposal.status == status)
        proposals = q.offset(offset).limit(limit).all()
        return [serialize(p) for p in proposals]
    finally:
        session.close()


@router.get("/{proposal_id}")
def get_proposal(proposal_id: int):
    session = get_sync_session()
    try:
        p = session.query(ImprovementProposal).filter_by(id=proposal_id).first()
        if not p:
            raise HTTPException(404, "Proposal not found")
        return serialize(p)
    finally:
        session.close()


@router.post("/{proposal_id}/approve")
def approve_proposal(proposal_id: int, req: ApproveRequest):
    """Approve a proposal → creates task_pool task (no execute).

    Guards:
    - Proposal must be in 'proposed' status
    - Approval record is updated synchronously
    - Created task has status=approval_required, not execute
    - Runtime proposals get requires_command_center=true
    """
    session = get_sync_session()
    try:
        p = session.query(ImprovementProposal).filter_by(id=proposal_id).first()
        if not p:
            raise HTTPException(404, "Proposal not found")
        if p.status != "proposed":
            raise HTTPException(400, f"Proposal status is '{p.status}', expected 'proposed'")

        # Update approval record
        approval = session.query(Approval).filter_by(id=p.approval_id).first()
        if approval:
            approval.status = "approved"
            approval.founder_decision = "approved"
            approval.founder_notes = req.founder_notes
            approval.decision_context = req.decision_context
            approval.approved_at = datetime.utcnow()

        # Update proposal status — first gate passed
        p.status = "approved"
        session.flush()

        # Create task_pool task — controlled action draft, not execute
        task = TaskPool(
            title=p.title,
            description=p.summary or p.rationale,
            source="improvement_proposal",
            source_id=f"improvement_proposal:{p.id}",
            status="approval_required",
            risk_level=p.risk_level,
            requires_approval=True,
            business_line=p.business_line,
            acceptance_criteria=json.dumps(
                {
                    "proposal_type": p.proposal_type,
                    "verification_plan": json.loads(p.verification_plan_json),
                },
                ensure_ascii=False,
            ),
        )
        session.add(task)
        session.flush()

        # Mark action created (second gate: Command Center / Founder execute)
        p.status = "action_created"
        p.created_task_id = task.id
        session.flush()

        # v0.8: Create execution request (dedup + policy check)
        try:
            from app.execution_bridge.policy import (
                validate_action, dry_run_required, has_active_request, log_blocked_action,
            )

            # Map proposal type to action type
            ACTION_MAP = {
                "retry_task_proposal": "create_retry_task",
                "context_update_proposal": "diagnose_task",
                "budget_review_proposal": "diagnose_task",
                "runtime_recovery_proposal": "run_dry_run_command",
                "memory_update_proposal": "generate_memory_update_draft",
            }
            action_type = ACTION_MAP.get(p.proposal_type)

            if action_type:
                # Dedup check
                existing_req = has_active_request(session, p.id)
                if existing_req:
                    return {
                        "proposal_id": p.id,
                        "status": p.status,
                        "task_id": task.id,
                        "execution_request_id": existing_req.id,
                        "note": "Execution request already exists",
                    }

                # Policy check
                policy = validate_action(action_type)
                if policy["allowed"]:
                    from app.models.execution_request import ExecutionRequest
                    er = ExecutionRequest(
                        source_type="improvement_proposal",
                        source_id=f"improvement_proposal:{p.id}",
                        proposal_id=p.id,
                        action_type=action_type,
                        action_payload_json=p.action_plan_json,
                        risk_level=p.risk_level,
                        dry_run_required=1 if dry_run_required(action_type) else 0,
                        status="pending_confirmation",
                    )
                    session.add(er)
                    session.flush()
                    execution_request_id = er.id
                else:
                    # Blocked action — log it but don't block approval
                    log_blocked_action(action_type, p.id, policy["reason"])
                    execution_request_id = None
            else:
                execution_request_id = None
        except ImportError:
            execution_request_id = None

        session.commit()

        return {
            "proposal_id": p.id,
            "status": p.status,
            "task_id": task.id,
            "execution_request_id": execution_request_id,
            "requires_command_center": bool(p.requires_command_center),
        }
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.post("/{proposal_id}/close")
def close_proposal(proposal_id: int, req: ProposalCloseRequest):
    """Close a proposal as success or failure.

    Rules:
    - closed_success: requires verification_result, generates Learning Candidate draft
    - closed_failed: generates nothing (optional in Sprint C)
    - rejected/dismissed: handled by reject endpoint
    """
    session = get_sync_session()
    try:
        p = session.query(ImprovementProposal).filter_by(id=proposal_id).first()
        if not p:
            raise HTTPException(404, "Proposal not found")
        if p.status != "action_created":
            raise HTTPException(
                400, f"Proposal status is '{p.status}', expected 'action_created'"
            )

        if req.result == "success":
            if not req.verification_result:
                raise HTTPException(
                    400, "closed_success requires verification_result"
                )
            p.status = "closed_success"
            p.verification_result_json = json.dumps(req.verification_result, ensure_ascii=False)
            p.verified_by = req.verified_by
            p.verified_at = datetime.utcnow()

            # Generate Learning Candidate draft (Sprint C)
            try:
                from app.improvement.learning import create_success_candidate
                candidate = create_success_candidate(session, p)
            except ImportError:
                pass  # learning module not yet created

        elif req.result == "failed":
            p.status = "closed_failed"
            p.verification_result_json = json.dumps(req.verification_result, ensure_ascii=False)
            p.verified_by = req.verified_by
            p.verified_at = datetime.utcnow()
        else:
            raise HTTPException(400, "result must be 'success' or 'failed'")

        session.commit()
        return {"proposal_id": p.id, "status": p.status}
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.post("/{proposal_id}/reject")
def reject_proposal(proposal_id: int, req: ProposalRejectRequest = ProposalRejectRequest()):
    """Reject a proposal (no action created)."""
    session = get_sync_session()
    try:
        p = session.query(ImprovementProposal).filter_by(id=proposal_id).first()
        if not p:
            raise HTTPException(404, "Proposal not found")
        if p.status != "proposed":
            raise HTTPException(
                400, f"Proposal status is '{p.status}', expected 'proposed'"
            )

        p.status = "rejected"

        # Sync approval record
        approval = session.query(Approval).filter_by(id=p.approval_id).first()
        if approval:
            approval.status = "rejected"
            approval.founder_decision = "rejected"
            approval.founder_notes = req.founder_notes

        session.commit()
        return {"proposal_id": p.id, "status": p.status}
    finally:
        session.close()
