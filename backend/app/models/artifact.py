# @PRODUCT Model — OS Core
from sqlalchemy import Column, String, Integer, Float
from app.models.base import Base

class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(String, primary_key=True)
    run_id = Column(String)
    business_line = Column(String, nullable=False)
    date = Column(String, nullable=False)
    artifact_path = Column(String, nullable=False)
    word_count = Column(Integer, default=0)
    file_size_bytes = Column(Integer, default=0)
    file_type = Column(String)
    validator_passed = Column(Integer)
    artifact_status = Column(String, default="created")
    cost_usd = Column(Float, default=0.0)
    model = Column(String)
    # Data source tracking fields
    data_source = Column(String, default="mock")    # real/mock/derived/partial
    source_name = Column(String, default="seed")     # specific source identifier
    source_path = Column(String)                      # original file path
    sync_batch_id = Column(String)                    # batch identifier for refresh
    last_synced_at = Column(String)                   # ISO timestamp of sync

    created_at = Column(String)
