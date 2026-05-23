"""Router for Knowledge Proposals — CRUD + Founder decide."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime, timezone
import logging

from app.database import get_async_session
from app.models.knowledge_proposal import KnowledgeProposal
from app.models.org_memory import OrgMemory
from app.schemas.knowledge_proposal import (
    KnowledgeProposalCreate,
    KnowledgeProposalResponse,
    KnowledgeProposalDecisionRequest,
    ProposalStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/memory", tags=["memory", "knowledge-proposals"])


@router.get("/knowledge-proposals", response_model=list[KnowledgeProposalResponse])
async def list_proposals(
    status: Optional[str] = None,
    proposal_type: Optional[str] = None,
    business_line: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
):
    """List knowledge proposals with filters."""
    stmt = select(KnowledgeProposal)
    if status:
        stmt = stmt.where(KnowledgeProposal.status == status)
    if proposal_type:
        stmt = stmt.where(KnowledgeProposal.proposal_type == proposal_type)
    if business_line:
        stmt = stmt.where(KnowledgeProposal.business_line == business_line)
    stmt = stmt.order_by(KnowledgeProposal.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("/knowledge-proposals", response_model=KnowledgeProposalResponse, status_code=201)
async def create_proposal(
    body: KnowledgeProposalCreate,
    session: AsyncSession = Depends(get_async_session),
):
    """Manually create a knowledge proposal."""
    # Check unique constraint on source_candidate_id
    if body.source_candidate_id:
        existing = await session.execute(
            select(KnowledgeProposal).where(
                KnowledgeProposal.source_candidate_id == body.source_candidate_id
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail=f"Proposal already exists for candidate {body.source_candidate_id}",
            )

    proposal = KnowledgeProposal(**body.model_dump())
    session.add(proposal)
    await session.commit()
    await session.refresh(proposal)
    return proposal


@router.patch("/knowledge-proposals/{proposal_id}/decide", response_model=KnowledgeProposalResponse)
async def decide_proposal(
    proposal_id: int,
    body: KnowledgeProposalDecisionRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """Founder decides on a knowledge proposal.

    - 'approved' → write to org_memory + mark proposal as committed
      (idempotent: if already committed, return 409)
    - 'revised' → update fields, keep status draft
    - 'rejected' → mark as expired
    """
    stmt = select(KnowledgeProposal).where(KnowledgeProposal.id == proposal_id)
    result = await session.execute(stmt)
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Knowledge proposal not found")

    decision = body.status
    if decision == "approved":
        # Idempotency check: already committed?
        if proposal.org_memory_id is not None:
            raise HTTPException(
                status_code=409,
                detail=f"Proposal {proposal_id} already committed to org_memory (id={proposal.org_memory_id}). Cannot re-commit.",
            )

        # Write to org_memory
        memory = OrgMemory(
            memory_type=proposal.target_memory_type,
            title=body.revised_title or proposal.title,
            summary=body.revised_summary or proposal.summary,
            content=proposal.structured_content,
            business_line=proposal.business_line,
            source_type="learning_candidate",
            source_candidate_id=proposal.source_candidate_id,
            status="active",
            version=1,
            confidence=0.85,  # default confidence for manual-approve path
        )
        session.add(memory)
        await session.flush()  # get memory.id

        # Mark proposal as committed
        proposal.status = "committed"
        proposal.org_memory_id = memory.id
        proposal.committed_at = datetime.now(timezone.utc)
        proposal.founder_notes = body.founder_notes

    elif decision == "revised":
        proposal.status = "draft"
        if body.founder_notes:
            proposal.founder_notes = body.founder_notes
        if body.revised_title:
            proposal.title = body.revised_title
        if body.revised_summary:
            proposal.summary = body.revised_summary

    elif decision == "rejected":
        proposal.status = "expired"
        if body.founder_notes:
            proposal.founder_notes = body.founder_notes

    else:
        raise HTTPException(status_code=400, detail=f"Unknown decision: {decision}")

    await session.commit()
    await session.refresh(proposal)
    return proposal
