from pydantic import BaseModel
from typing import Optional

class ReviewCreate(BaseModel):
    task_id: int
    result: str  # pass / revision_required / blocked
    artifact_id: Optional[str] = None
    review_notes: Optional[str] = None
    next_action: Optional[str] = None
    reviewed_by: str = "founder"

class ReviewResponse(BaseModel):
    id: int
    task_id: int
    result: str
    artifact_id: Optional[str] = None
    review_notes: Optional[str] = None
    next_action: Optional[str] = None
    reviewed_by: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
