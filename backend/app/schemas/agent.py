from pydantic import BaseModel
from typing import Optional

class AgentResponse(BaseModel):
    id: str
    name: str
    identity: Optional[str] = None
    workspace: Optional[str] = None
    model: Optional[str] = None
    routing_rules: int = 0
    agent_type: str = "openclaw"
    role: Optional[str] = None
    skills: Optional[str] = None
    status: str = "offline"
    discovery_status: str = "discovered"
    activity_status: str = "inactive"
    health_status: str = "ok"
    total_cost_usd: float = 0.0
    last_active_at: Optional[str] = None
    total_runs: int = 0
    recent_task: Optional[str] = None

class AgentPatchRequest(BaseModel):
    skills: Optional[str] = None
    capabilities: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
