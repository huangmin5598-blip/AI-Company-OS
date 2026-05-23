# @PRODUCT Model — OS Core
from sqlalchemy import Column, String, Integer, Text, DateTime, func
from app.models.base import Base


class MonitorInsight(Base):
    """Monitor Agent analysis result — stores failure patterns, gap analysis, and improvement suggestions."""

    __tablename__ = "monitor_insights"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Insight type
    insight_type = Column(String, nullable=False, index=True)
    # "failure_cluster" — a group of similar failures
    # "skill_gap" — a skill needed but no agent has it
    # "stalled_task" — in_progress for too long
    # "cost_anomaly" — unusual cost spike
    # "improvement_suggestion" — general improvement

    # What the insight is about
    title = Column(String, nullable=False)
    description = Column(Text)

    # Severity: critical / warning / info
    severity = Column(String, default="info")

    # Structured data (JSON)
    details = Column(Text)
    # For failure_cluster: {"failure_reason": "...", "agent_id": "...", "count": 5, "sample_ids": [1,2,3], "suggestion": "..."}
    # For skill_gap: {"skill": "...", "agents_with": [], "missing_count": 3, "suggestion": "..."}
    # For stalled_task: {"task_id": 5, "agent_id": "...", "hours_stalled": 3.5}

    # Status: new / acknowledged / resolved / dismissed
    status = Column(String, default="new")

    # Auto-resolve tracking
    source = Column(String)  # "monitor_agent_v1"
    resolved_at = Column(DateTime)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
