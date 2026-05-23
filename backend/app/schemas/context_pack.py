from pydantic import BaseModel
from typing import Optional

class ContextPackCreate(BaseModel):
    founder_intent: Optional[str] = None
    business_line_state: Optional[str] = None
    related_runs: Optional[str] = None
    related_artifacts: Optional[str] = None
    known_failures: Optional[str] = None
    relevant_rules: Optional[str] = None
    constraints: Optional[str] = None
    forbidden_actions: Optional[str] = None
    budget_limit: Optional[float] = None
    acceptance_criteria: Optional[str] = None
    referenced_knowledge: Optional[str] = None
    auto_generated: bool = False

class ContextPackResponse(BaseModel):
    id: int
    task_id: int
    founder_intent: Optional[str] = None
    business_line_state: Optional[str] = None
    related_runs: Optional[str] = None
    related_artifacts: Optional[str] = None
    known_failures: Optional[str] = None
    relevant_rules: Optional[str] = None
    constraints: Optional[str] = None
    forbidden_actions: Optional[str] = None
    budget_limit: Optional[float] = None
    acceptance_criteria: Optional[str] = None
    referenced_knowledge: Optional[str] = None
    auto_generated: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
