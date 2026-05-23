# @PRODUCT Model — OS Core
from sqlalchemy import Column, String, Integer, Text, DateTime, func
from app.models.base import Base


class MonitorRun(Base):
    """A single monitor scan execution record."""

    __tablename__ = "monitor_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(DateTime, nullable=False, default=func.now())
    finished_at = Column(DateTime)
    status = Column(String, nullable=False, default="running")
    # success / failed / partial
    summary = Column(Text)
    findings_count = Column(Integer, default=0)
    alerts_created = Column(Integer, default=0)
    tasks_created = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
