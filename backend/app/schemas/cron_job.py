from pydantic import BaseModel
from typing import Optional

class CronJobResponse(BaseModel):
    id: str
    name: str
    agent_id: Optional[str] = None
    business_line_id: Optional[str] = None
    schedule_expr: Optional[str] = None
    enabled: bool = False
    last_run_at: Optional[str] = None
    last_status: Optional[str] = None
    consecutive_errors: int = 0
    last_error: Optional[str] = None
