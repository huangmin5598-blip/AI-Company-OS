# @PRODUCT Model — OS Core
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, func
from app.models.base import Base


class RuntimeHeartbeat(Base):
    """Health check record for a runtime."""

    __tablename__ = "runtime_heartbeats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    runtime_id = Column(String, ForeignKey("runtime_registry.runtime_id"), nullable=False, index=True)
    status = Column(String, nullable=False)
    # online / degraded / offline / unknown
    message = Column(Text)
    latency_ms = Column(Integer)
    capabilities_count = Column(Integer, default=0)
    checked_at = Column(DateTime, nullable=False, default=func.now())
