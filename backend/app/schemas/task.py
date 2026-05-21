from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    agent_id: str = "main"
    priority: str = "medium"
    source: str = "command"
    required_skills: Optional[str] = None  # JSON array
    success_criteria: Optional[str] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    status: Optional[str] = None
    result_summary: Optional[str] = None
    error_message: Optional[str] = None
    failure_reason: Optional[str] = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    agent_id: str
    status: str
    priority: str
    source: Optional[str] = None
    required_skills: Optional[str] = None
    success_criteria: Optional[str] = None
    failure_reason: Optional[str] = None
    result_summary: Optional[str] = None
    error_message: Optional[str] = None
    cost_usd: Optional[float] = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskMessageResponse(BaseModel):
    id: int
    task_id: int
    role: str
    content: str
    msg_metadata: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class CommandRequest(BaseModel):
    instruction: str
    agent_id: str = "main"
    priority: str = "medium"
    required_skills: Optional[str] = None
    success_criteria: Optional[str] = None


class CommandResponse(BaseModel):
    task: TaskResponse
    message: str


class AgentPatchRequest(BaseModel):
    skills: Optional[str] = None
    capabilities: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
