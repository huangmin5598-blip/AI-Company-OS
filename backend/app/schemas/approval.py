from pydantic import BaseModel
from typing import Optional

class ApprovalCreate(BaseModel):
    target_type: str  # task / command / learning_candidate
    target_id: int
    risk_level: str = "medium"
    reason: Optional[str] = None
    decision_context: Optional[str] = None

class ApprovalDecisionRequest(BaseModel):
    founder_decision: str  # approved / revised / rejected / deferred
    founder_notes: Optional[str] = None

class ApprovalResponse(BaseModel):
    id: int
    target_type: str
    target_id: int
    risk_level: str
    reason: Optional[str] = None
    founder_decision: Optional[str] = None
    founder_notes: Optional[str] = None
    decision_context: Optional[str] = None
    status: str
    approved_at: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
