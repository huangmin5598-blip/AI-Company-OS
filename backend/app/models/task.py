# @PRODUCT Model — OS Core
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, func
from app.models.base import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(Text)

    # Agent assignment
    agent_id = Column(String, nullable=False, default="main")

    # Status: pending / in_progress / completed / failed / cancelled
    status = Column(String, default="pending")
    priority = Column(String, default="medium")  # low/medium/high/critical
    source = Column(String)  # command/manual/cron

    # v0.2 new fields
    required_skills = Column(Text)   # JSON array ["skill1","skill2"]
    success_criteria = Column(Text)  # e.g. "文章 > 2000字，3个来源"
    failure_reason = Column(Text)    # e.g. "API 限频"

    # Results
    result_summary = Column(Text)
    error_message = Column(Text)
    cost_usd = Column(Float, default=0.0)    # Real cost from token usage

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class TaskMessage(Base):
    __tablename__ = "task_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, nullable=False)  # FK -> tasks.id
    role = Column(String, nullable=False)      # user/agent/system
    content = Column(Text, nullable=False)
    msg_metadata = Column("metadata", Text)       # JSON (token用语、耗时等)

    created_at = Column(DateTime, server_default=func.now())
