from pydantic import BaseModel
from typing import Optional


class GoalSessionCreate(BaseModel):
    source_channel: str = "cc_panel"
    raw_goal: str
    client_request_id: Optional[str] = None
    interpreted_goal: Optional[str] = None
    goal_type: Optional[str] = None
    business_line: Optional[str] = None
    priority: str = "medium"
    risk_level: str = "medium"
    status: str = "draft"
    decomposition_json: Optional[str] = None
    task_ids_json: Optional[str] = None
    approval_ids_json: Optional[str] = None
    model_used: Optional[str] = None
    confidence: Optional[float] = None
    schema_version: str = "v0.3.0"
    error_message: Optional[str] = None


class GoalSessionResponse(BaseModel):
    id: int
    source_channel: str = "cc_panel"
    raw_goal: str
    client_request_id: Optional[str] = None
    interpreted_goal: Optional[str] = None
    goal_type: Optional[str] = None
    business_line: Optional[str] = None
    priority: str = "medium"
    risk_level: str = "medium"
    status: str = "draft"
    decomposition_json: Optional[str] = None
    task_ids_json: Optional[str] = None
    approval_ids_json: Optional[str] = None
    model_used: Optional[str] = None
    confidence: Optional[float] = None
    schema_version: str = "v0.3.0"
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
