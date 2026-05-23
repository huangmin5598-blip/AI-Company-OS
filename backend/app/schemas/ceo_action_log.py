# @PRODUCT Schema — OS Core
from pydantic import BaseModel
from typing import Optional


class CeoActionLogCreate(BaseModel):
    source_channel: str = "cc_panel"
    raw_user_message: str
    intent_type: str  # goal_intake / approval_action
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    action_taken: Optional[str] = None
    payload_json: Optional[str] = None
    result_status: str = "success"
    result_summary: Optional[str] = None
    confidence: Optional[float] = None
    requires_confirmation: bool = False
    confirmed_by_founder: bool = False


class CeoActionLogResponse(BaseModel):
    id: int
    source_channel: str = "cc_panel"
    raw_user_message: str
    intent_type: str
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    action_taken: Optional[str] = None
    payload_json: Optional[str] = None
    result_status: str = "success"
    result_summary: Optional[str] = None
    confidence: Optional[float] = None
    requires_confirmation: bool = False
    confirmed_by_founder: bool = False
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
