# @PRODUCT Model — OS Core
from sqlalchemy import Column, String, Integer, Float, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.models.base import Base


class CeoActionLog(Base):
    __tablename__ = "ceo_action_logs"

    id = Column(Integer, primary_key=True)
    source_channel = Column(String, default="cc_panel")
    raw_user_message = Column(Text, nullable=False)
    intent_type = Column(String, nullable=False)            # goal_intake / approval_action
    target_type = Column(String, nullable=True)              # goal_session / task / approval / learning_candidate
    target_id = Column(Integer, nullable=True)
    action_taken = Column(String, nullable=True)             # decomposed / approved / rejected / revised / deferred / cancelled / failed
    payload_json = Column(Text, nullable=True)
    result_status = Column(String, default="success")        # success / failed / ambiguous / cancelled
    result_summary = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    requires_confirmation = Column(Boolean, default=False)
    confirmed_by_founder = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
