from sqlalchemy import Column, String, Integer, Float, Text, DateTime
from sqlalchemy.sql import func
from app.models.base import Base


class GoalSession(Base):
    __tablename__ = "goal_sessions"

    id = Column(Integer, primary_key=True)
    source_channel = Column(String, default="cc_panel")  # cc_panel / feishu
    raw_goal = Column(Text, nullable=False)
    client_request_id = Column(String, nullable=True)     # optional for idempotency
    interpreted_goal = Column(String, nullable=True)
    goal_type = Column(String, nullable=True)              # repair / growth / research / build / review / ops
    business_line = Column(String, nullable=True)
    priority = Column(String, default="medium")
    risk_level = Column(String, default="medium")
    status = Column(String, default="draft")               # draft / decomposed / committed / cancelled / failed
    decomposition_json = Column(Text, nullable=True)
    task_ids_json = Column(Text, nullable=True)            # JSON array
    approval_ids_json = Column(Text, nullable=True)        # JSON array
    model_used = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    schema_version = Column(String, default="v0.3.0")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
