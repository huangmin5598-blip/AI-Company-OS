# @PRODUCT Schema — OS Core
from pydantic import BaseModel
from typing import Optional

class LoopStatsResponse(BaseModel):
    total_tasks: int = 0
    alert_pooled_count: int = 0
    approval_rate: float = 0.0
    review_distribution: dict = {}
    candidate_count: int = 0
    candidate_approved_count: int = 0
    pending_approval_tasks: int = 0
    pending_candidates: int = 0
    recent_task_trend: list = []
