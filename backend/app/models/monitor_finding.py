# @PRODUCT Model — OS Core
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, func
from app.models.base import Base


class MonitorFinding(Base):
    """A single finding from a monitor scan."""

    __tablename__ = "monitor_findings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    monitor_run_id = Column(Integer, ForeignKey("monitor_runs.id"), nullable=False)
    finding_type = Column(String, nullable=False, index=True)
    # stuck_task / cost_spike / error_rate / runtime_health
    severity = Column(String, nullable=False, default="info")
    # info / warning / critical
    title = Column(String, nullable=False)
    summary = Column(Text)
    evidence_json = Column(Text)
    # JSON string
    status = Column(String, nullable=False, default="open")
    # open / acknowledged / dismissed / converted
    source_id = Column(String)
    # e.g. "task:42", "cost:snapshot:5"
    alert_id = Column(Integer)
    task_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
