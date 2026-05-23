# @PRODUCT Model — OS Core
from sqlalchemy import Column, String, Integer, Float, Text, DateTime
from sqlalchemy.sql import func
from app.models.base import Base

class TaskPool(Base):
    __tablename__ = "task_pool"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    business_line = Column(String, nullable=True)
    source = Column(String, nullable=False)  # alert / command / manual / cron
    source_id = Column(String, nullable=True)

    # Status machine: draft → ready → approval_required → approved → running → review → done
    status = Column(String, default="draft")

    priority = Column(String, default="medium")       # low / medium / high / critical
    risk_level = Column(String, default="medium")      # low / medium / high
    assigned_agent = Column(String, nullable=True)
    context_pack_id = Column(Integer, nullable=True)   # FK → context_packs.id
    requires_approval = Column(Integer, default=1)

    acceptance_criteria = Column(Text, nullable=True)
    result_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    cost_usd = Column(Float, default=0.0)
    failure_reason = Column(Text, nullable=True)

    # Reserved fields (v0.6+)
    execution_runtime = Column(String, default="openclaw")
    execution_mode = Column(String, default="standard")
    execution_workspace = Column(String, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)
