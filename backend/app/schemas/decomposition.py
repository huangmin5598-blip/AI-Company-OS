from pydantic import BaseModel
from typing import Optional


class ContextPackProposal(BaseModel):
    founder_intent: Optional[str] = None
    related_sources: Optional[list[str]] = None
    known_failures: Optional[list[str]] = None
    constraints: Optional[str] = None


class TaskProposal(BaseModel):
    title: str
    why: str
    task_type: str
    assigned_agent: Optional[str] = None
    risk_level: str
    priority: str
    acceptance_criteria: Optional[str] = None
    context_pack: Optional[ContextPackProposal] = None


class CommitDecompositionRequest(BaseModel):
    client_request_id: Optional[str] = None
    source_channel: str = "cc_panel"
    raw_goal: str
    interpreted_goal: str
    goal_type: str
    business_line: Optional[str] = None
    risk_level: str = "medium"
    priority: str = "medium"
    model_used: Optional[str] = None
    confidence: Optional[float] = None
    tasks: list[TaskProposal]


class CommitDecompositionResponse(BaseModel):
    goal_session_id: int
    task_ids: list[int]
    approval_ids: list[int]
    status: str
