from pydantic import BaseModel
from typing import Optional

class LearningCandidateCreate(BaseModel):
    source_type: str  # failure / tool_gap / context_update / rule_update / asset_candidate
    source_id: Optional[str] = None
    source_summary: Optional[str] = None
    candidate_type: str  # failure_pattern / tool_gap / context_update / rule_update / sop_update / asset
    summary: Optional[str] = None
    recommendation: Optional[str] = None

class LearningCandidateDecisionRequest(BaseModel):
    approval_status: str  # approved / rejected / approved_for_knowledge_update
    approved_by: Optional[str] = None

class LearningCandidateResponse(BaseModel):
    id: int
    source_type: str
    source_id: Optional[str] = None
    source_summary: Optional[str] = None
    candidate_type: str
    summary: Optional[str] = None
    recommendation: Optional[str] = None
    approval_status: str
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
