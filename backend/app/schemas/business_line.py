# @PRODUCT Schema — OS Core
from pydantic import BaseModel
from typing import Optional

class BusinessLineResponse(BaseModel):
    id: str
    name: str
    status: str = "unknown"
    total_runs: int = 0
    failed_runs: int = 0
    total_cost_usd: float = 0.0
    last_run_date: Optional[str] = None
    last_run_result: Optional[str] = None
    recent_artifacts: list = []
