from sqlalchemy import Column, String, Integer, Text
from app.models.base import Base

class RefreshLog(Base):
    __tablename__ = "refresh_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    refreshed_at = Column(String, nullable=False)
    batch_id = Column(String)
    status = Column(String)
    summary = Column(Text)
    created_at = Column(String)
