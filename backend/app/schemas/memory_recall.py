# @PRODUCT Schema — OS Core
"""Pydantic schemas for memory recall (CEO Agent)."""
from pydantic import BaseModel
from typing import Optional


class MemoryRecallRequest(BaseModel):
    goal_summary: str
    business_line: Optional[str] = None


class RecalledMemory(BaseModel):
    memory_id: int
    title: str
    summary: Optional[str] = None
    memory_type: str
    confidence: float


class MemoryRecallResponse(BaseModel):
    memories: list[RecalledMemory] = []
    recall_query: str = ""
    total: int = 0
