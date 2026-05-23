# @PRODUCT Model — OS Core
from sqlalchemy import Column, String, Integer, Float, Text
from app.models.base import Base

class BusinessLine(Base):
    __tablename__ = "business_lines"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, default="unknown")

    primary_agent_id = Column(String)
    agent_ids = Column(Text)
    workflow_id = Column(String)
    triggers = Column(Text)

    total_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)
    last_run_date = Column(String)
    last_run_result = Column(String)
    created_at = Column(String)
    updated_at = Column(String)
