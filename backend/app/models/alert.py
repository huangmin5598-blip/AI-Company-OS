from sqlalchemy import Column, String, Integer, Text
from app.models.base import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    severity = Column(String)
    title = Column(String, nullable=False)
    description = Column(Text)
    source = Column(String)
    source_id = Column(String)
    resolved = Column(Integer, default=0)
    created_at = Column(String)
