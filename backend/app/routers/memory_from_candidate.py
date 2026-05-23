"""Router for idempotent from-learning-candidate → proposal generation."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import logging

from app.database import get_async_session
from app.models.learning_candidate import LearningCandidate
from app.models.knowledge_proposal import KnowledgeProposal
from app.schemas.knowledge_proposal import KnowledgeProposalResponse, ProposalType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/memory", tags=["memory", "learning-candidates"])

# Mapping from candidate_type → target_memory_type / proposal_type
CANDIDATE_TYPE_MAP = {
    "failure_pattern": "failure_pattern",
    "tool_gap": "tool_gap",
    "context_update": "context_update",
    "rule_update": "sop_hint",
    "sop_update": "sop_hint",
    "asset_candidate": "context_update",  # best guess
}


@router.post(
    "/from-learning-candidate/{candidate_id}",
    response_model=KnowledgeProposalResponse,
    status_code=201,
)
async def from_learning_candidate(
    candidate_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """Generate a knowledge proposal from an approved learning candidate.

    Idempotent: repeated calls return existing proposal (200) instead of creating
    a new one (201). Powered by source_candidate_id unique constraint.
    """
    # 1. Validate candidate exists and is approved
    result = await session.execute(
        select(LearningCandidate).where(LearningCandidate.id == candidate_id)
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Learning candidate not found")

    if candidate.approval_status not in ("approved", "approved_for_knowledge_update"):
        raise HTTPException(
            status_code=400,
            detail=f"Candidate {candidate_id} is not approved (status={candidate.approval_status}). Cannot generate proposal.",
        )

    # 2. Idempotency check: proposal already exists for this candidate
    existing_result = await session.execute(
        select(KnowledgeProposal).where(
            KnowledgeProposal.source_candidate_id == candidate_id
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        # 200 — return existing, don't create new
        return JSONResponse(
            status_code=200,
            content=KnowledgeProposalResponse.model_validate(existing).model_dump(mode="json"),
        )

    # 3. Generate proposal from candidate data
    target_type = CANDIDATE_TYPE_MAP.get(
        candidate.candidate_type, "context_update"
    )

    # Build a simple title from summary
    title = candidate.summary or candidate.source_summary or f"Memory from Candidate #{candidate_id}"
    if len(title) > 200:
        title = title[:197] + "..."

    # Build structured_content from recommendation
    structured_content = candidate.recommendation

    proposal = KnowledgeProposal(
        source_candidate_id=candidate.id,
        proposal_type=target_type,
        title=title,
        summary=candidate.summary,
        structured_content=structured_content,
        target_memory_type=target_type,
        business_line=None,  # inferred from candidate context if available
        status="draft",
    )
    session.add(proposal)
    await session.commit()
    await session.refresh(proposal)
    return proposal
