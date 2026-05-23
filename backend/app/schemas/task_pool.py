from pydantic import BaseModel
from typing import Optional

class TaskPoolCreate(BaseModel):
    title: str
    description: Optional[str] = None
    business_line: Optional[str] = None
    source: str = "manual"  # alert / command / manual / cron
    source_id: Optional[str] = None
    status: str = "draft"
    priority: str = "medium"
    risk_level: str = "medium"
    assigned_agent: Optional[str] = None
    requires_approval: bool = True
    acceptance_criteria: Optional[str] = None
    execution_runtime: str = "openclaw"
    execution_mode: str = "standard"
    execution_workspace: Optional[str] = None

class TaskPoolUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    business_line: Optional[str] = None
    source: Optional[str] = None
    source_id: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    risk_level: Optional[str] = None
    assigned_agent: Optional[str] = None
    requires_approval: Optional[bool] = None
    acceptance_criteria: Optional[str] = None
    result_summary: Optional[str] = None
    error_message: Optional[str] = None
    cost_usd: Optional[float] = None
    failure_reason: Optional[str] = None
    execution_runtime: Optional[str] = None
    execution_mode: Optional[str] = None
    execution_workspace: Optional[str] = None
    completed_at: Optional[str] = None

class TaskPoolResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    business_line: Optional[str] = None
    source: str
    source_id: Optional[str] = None
    status: str
    priority: str
    risk_level: str
    assigned_agent: Optional[str] = None
    context_pack_id: Optional[int] = None
    requires_approval: bool
    acceptance_criteria: Optional[str] = None
    result_summary: Optional[str] = None
    error_message: Optional[str] = None
    cost_usd: float = 0.0
    failure_reason: Optional[str] = None
    execution_runtime: str = "openclaw"
    execution_mode: str = "standard"
    execution_workspace: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None

    class Config:
        from_attributes = True
