# @PRODUCT Router — OS Core
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime
from app.database import get_sync_session
from app.models.learning_candidate import LearningCandidate
from app.schemas.learning_candidate import (
    LearningCandidateCreate,
    LearningCandidateDecisionRequest,
    LearningCandidateResponse,
)

router = APIRouter(tags=["Learning Candidates"])


@router.get("/api/v1/learning-candidates", response_model=list[LearningCandidateResponse])
def list_learning_candidates(
    status: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None),
    candidate_type: Optional[str] = Query(None),
):
    session = get_sync_session()
    try:
        query = session.query(LearningCandidate)
        if status:
            query = query.filter(LearningCandidate.approval_status == status)
        if source_type:
            query = query.filter(LearningCandidate.source_type == source_type)
        if candidate_type:
            query = query.filter(LearningCandidate.candidate_type == candidate_type)

        candidates = query.order_by(LearningCandidate.created_at.desc()).all()
        return [_lc_to_response(c) for c in candidates]
    finally:
        session.close()


@router.post("/api/v1/learning-candidates", response_model=LearningCandidateResponse, status_code=201)
def create_learning_candidate(body: LearningCandidateCreate):
    session = get_sync_session()
    try:
        lc = LearningCandidate(
            source_type=body.source_type,
            source_id=body.source_id,
            source_summary=body.source_summary,
            candidate_type=body.candidate_type,
            summary=body.summary,
            recommendation=body.recommendation,
            approval_status="pending_approval",
        )
        session.add(lc)
        session.commit()
        session.refresh(lc)
        return _lc_to_response(lc)
    finally:
        session.close()


@router.patch("/api/v1/learning-candidates/{candidate_id}/decide", response_model=LearningCandidateResponse)
def decide_learning_candidate(candidate_id: int, body: LearningCandidateDecisionRequest):
    session = get_sync_session()
    try:
        lc = session.query(LearningCandidate).filter(LearningCandidate.id == candidate_id).first()
        if not lc:
            raise HTTPException(status_code=404, detail="Learning candidate not found")

        if lc.approval_status != "pending_approval":
            raise HTTPException(
                status_code=400,
                detail=f"Candidate already has status: {lc.approval_status}"
            )

        lc.approval_status = body.approval_status
        lc.approved_by = body.approved_by

        if body.approval_status in ("approved", "approved_for_knowledge_update"):
            lc.approved_at = datetime.utcnow()

        session.commit()
        session.refresh(lc)
        return _lc_to_response(lc)
    finally:
        session.close()


def _lc_to_response(lc: LearningCandidate) -> LearningCandidateResponse:
    return LearningCandidateResponse(
        id=lc.id,
        source_type=lc.source_type,
        source_id=lc.source_id,
        source_summary=lc.source_summary,
        candidate_type=lc.candidate_type,
        summary=lc.summary,
        recommendation=lc.recommendation,
        approval_status=lc.approval_status,
        approved_by=lc.approved_by,
        approved_at=lc.approved_at.isoformat() if lc.approved_at else None,
        created_at=lc.created_at.isoformat() if lc.created_at else None,
    )
