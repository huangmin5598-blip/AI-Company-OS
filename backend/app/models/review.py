# @PRODUCT Model — OS Core
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.sql import func
from app.models.base import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, nullable=False)   # FK → task_pool.id
    result = Column(String, nullable=False)     # pass / revision_required / blocked
    artifact_id = Column(String, nullable=True)
    review_notes = Column(Text, nullable=True)
    next_action = Column(Text, nullable=True)
    reviewed_by = Column(String, default="founder")
    created_at = Column(DateTime, server_default=func.now())
