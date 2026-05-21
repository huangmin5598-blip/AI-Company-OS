from sqlalchemy import Column, String, Integer, Float, Text
from app.models.base import Base

class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    identity = Column(String)
    workspace = Column(String)
    model = Column(String)
    routing_rules = Column(Integer, default=0)
    is_default = Column(Integer, default=0)

    # Reserved: multi-runtime
    agent_type = Column(String, default="openclaw")
    runtime_id = Column(String)
    role = Column(String)
    capabilities = Column(Text)
    skills = Column(Text)          # JSON array of skill names
    tools_summary = Column(Text)
    memory_path = Column(String)
    identity_path = Column(String)

    # Status
    status = Column(String, default="offline")
    total_cost_usd = Column(Float, default=0.0)
    last_active_at = Column(String)
    created_at = Column(String)
    updated_at = Column(String)
