# @PRODUCT Model — OS Core
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.sql import func
from app.models.base import Base

class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True)
    target_type = Column(String, nullable=False)      # task / command / learning_candidate
    target_id = Column(Integer, nullable=False)
    risk_level = Column(String, default="medium")      # low / medium / high
    reason = Column(Text, nullable=True)
    founder_decision = Column(String, nullable=True)   # approved / revised / rejected / deferred
    founder_notes = Column(Text, nullable=True)
    decision_context = Column(Text, nullable=True)     # JSON: system state snapshot
    status = Column(String, default="approval_requested")
    # status values: approval_requested / approved / rejected / expired / executed / cancelled
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
