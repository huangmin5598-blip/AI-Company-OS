"""Pydantic schemas for OrgMemory."""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime


class MemoryType(str, Enum):
    failure_pattern = "failure_pattern"
    decision_pattern = "decision_pattern"
    tool_gap = "tool_gap"
    context_update = "context_update"
    sop_hint = "sop_hint"


class MemoryStatus(str, Enum):
    active = "active"
    superseded = "superseded"
    expired = "expired"
    archived = "archived"


class OrgMemoryCreate(BaseModel):
    memory_type: MemoryType
    title: str
    summary: Optional[str] = None
    content: Optional[str] = None
    business_line: Optional[str] = None
    tags: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    source_candidate_id: Optional[int] = None
    source_task_id: Optional[int] = None
    source_review_id: Optional[int] = None
    source_goal_session_id: Optional[int] = None
    confidence: Optional[float] = None
    status: MemoryStatus = MemoryStatus.active
    supersedes_memory_id: Optional[int] = None
    export_status: Optional[str] = "not_exported"


class OrgMemoryResponse(BaseModel):
    id: int
    memory_type: str
    title: str
    summary: Optional[str] = None
    content: Optional[str] = None
    business_line: Optional[str] = None
    tags: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    source_candidate_id: Optional[int] = None
    source_task_id: Optional[int] = None
    source_review_id: Optional[int] = None
    source_goal_session_id: Optional[int] = None
    confidence: Optional[float] = None
    status: str
    version: int
    supersedes_memory_id: Optional[int] = None
    export_status: Optional[str] = None
    knowledge_os_path: Optional[str] = None
    knowledge_os_slug: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MemorySearchResult(BaseModel):
    id: int
    memory_type: str
    title: str
    summary: Optional[str] = None
    snippet: Optional[str] = None
    business_line: Optional[str] = None
    tags: Optional[str] = None
    status: str
    version: int
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    source_candidate_id: Optional[int] = None
    source_task_id: Optional[int] = None
    source_review_id: Optional[int] = None
    source_goal_session_id: Optional[int] = None
    created_at: Optional[datetime] = None
