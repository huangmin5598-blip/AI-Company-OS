# @PRODUCT Schema — OS Core
from pydantic import BaseModel

class StatsResponse(BaseModel):
    agent_count: int = 0
    online_agents: int = 0
    busy_agents: int = 0
    offline_agents: int = 0
    business_line_count: int = 0
    running_lines: int = 0
    error_lines: int = 0
    today_cost_usd: float = 0.0
    month_cost_usd: float = 0.0
    total_executions: int = 0
    failed_executions: int = 0
    pending_alerts: int = 0
