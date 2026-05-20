from sqlalchemy import Column, String, Integer, Text
from app.models.base import Base

class SessionEvent(Base):
    """Reserved: future session event tracking (Anthropic 4-layer). v0.1 not populated."""
    __tablename__ = "session_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    agent_id = Column(String)
    payload = Column(Text)
    created_at = Column(String)
