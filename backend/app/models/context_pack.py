# @PRODUCT Model — OS Core
from sqlalchemy import Column, String, Integer, Float, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.models.base import Base

class ContextPack(Base):
    __tablename__ = "context_packs"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, nullable=False)  # FK → task_pool.id (1:1)
    founder_intent = Column(Text, nullable=True)
    business_line_state = Column(Text, nullable=True)
    related_runs = Column(Text, nullable=True)       # JSON array
    related_artifacts = Column(Text, nullable=True)  # JSON array
    known_failures = Column(Text, nullable=True)     # JSON array
    relevant_rules = Column(Text, nullable=True)     # JSON array
    constraints = Column(Text, nullable=True)
    forbidden_actions = Column(Text, nullable=True)
    budget_limit = Column(Float, nullable=True)
    acceptance_criteria = Column(Text, nullable=True)
    referenced_knowledge = Column(Text, nullable=True)  # JSON: [{title, path, slug, reason}]
    referenced_memory_ids = Column(Text, nullable=True)  # JSON: [memory.id, ...]  — v0.4 Company Memory
    auto_generated = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
