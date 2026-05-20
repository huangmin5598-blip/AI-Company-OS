from sqlalchemy import Column, String, Integer, Float, Text
from app.models.base import Base

class CostSnapshot(Base):
    __tablename__ = "cost_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String, nullable=False)
    agent_id = Column(String)
    model = Column(String)
    provider = Column(String)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    fallback_count = Column(Integer, default=0)
    result_status = Column(String)
    task_hint = Column(String)
    created_at = Column(String)
