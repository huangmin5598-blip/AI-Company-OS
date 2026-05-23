"""Pydantic schemas for KnowledgeProposal."""
from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import datetime


class ProposalType(str, Enum):
    failure_pattern = "failure_pattern"
    decision_pattern = "decision_pattern"
    tool_gap = "tool_gap"
    context_update = "context_update"
    sop_hint = "sop_hint"


class ProposalStatus(str, Enum):
    draft = "draft"
    committed = "committed"
    revised = "revised"
    rejected = "rejected"
    expired = "expired"


class KnowledgeProposalCreate(BaseModel):
    source_candidate_id: int
    proposal_type: ProposalType
    title: str
    summary: Optional[str] = None
    structured_content: Optional[str] = None
    target_memory_type: ProposalType
    business_line: Optional[str] = None


class KnowledgeProposalResponse(BaseModel):
    id: int
    source_candidate_id: int
    proposal_type: str
    title: str
    summary: Optional[str] = None
    structured_content: Optional[str] = None
    target_memory_type: str
    business_line: Optional[str] = None
    status: str
    org_memory_id: Optional[int] = None
    committed_at: Optional[datetime] = None
    founder_notes: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class KnowledgeProposalDecisionRequest(BaseModel):
    status: str  # approved / revised / rejected
    founder_notes: Optional[str] = None
    revised_title: Optional[str] = None
    revised_summary: Optional[str] = None
