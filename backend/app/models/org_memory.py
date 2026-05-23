"""OrgMemory model — Company Memory (L3)."""
from sqlalchemy import Column, String, Integer, Float, Text, DateTime
from sqlalchemy.sql import func
from app.models.base import Base


class OrgMemory(Base):
    __tablename__ = "org_memory"

    id = Column(Integer, primary_key=True)
    memory_type = Column(String, nullable=False)
    # failure_pattern / decision_pattern / tool_gap / context_update / sop_hint
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    business_line = Column(String, nullable=True)
    tags = Column(Text, nullable=True)                              # JSON array
    source_type = Column(String, nullable=True)                      # learning_candidate / review / task / goal_session
    source_id = Column(String, nullable=True)
    source_candidate_id = Column(Integer, nullable=True)             # FK
    source_task_id = Column(Integer, nullable=True)                  # FK
    source_review_id = Column(Integer, nullable=True)                # FK
    source_goal_session_id = Column(Integer, nullable=True)          # FK
    confidence = Column(Float, nullable=True)
    status = Column(String, default="active")                        # active / superseded / expired / archived
    version = Column(Integer, default=1)
    supersedes_memory_id = Column(Integer, nullable=True)            # FK → org_memory.id
    export_status = Column(String, default="not_exported")           # not_exported / exported / pending / failed
    knowledge_os_path = Column(String, nullable=True)
    knowledge_os_slug = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
