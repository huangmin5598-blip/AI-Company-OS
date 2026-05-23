# @PRODUCT Model — OS Core
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
    # Data source tracking fields
    data_source = Column(String, default="mock")    # real/mock/derived/partial
    source_name = Column(String, default="seed")     # specific source identifier
    source_path = Column(String)                      # original file path
    sync_batch_id = Column(String)                    # batch identifier for refresh
    last_synced_at = Column(String)                   # ISO timestamp of sync

    created_at = Column(String)
