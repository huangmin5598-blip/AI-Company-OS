from pydantic import BaseModel
from typing import Optional

class CostSummaryResponse(BaseModel):
    group: str
    items: list = []

class CostSummaryItem(BaseModel):
    name: str
    total_calls: int = 0
    total_cost_usd: float = 0.0
    avg_cost_per_call: float = 0.0

class DailyCostResponse(BaseModel):
    date: str
    entries: list = []
