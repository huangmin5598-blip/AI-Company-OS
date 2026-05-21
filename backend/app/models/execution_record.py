from sqlalchemy import Column, String, Integer, Float, Text, Index
from app.models.base import Base

class ExecutionRecord(Base):
    __tablename__ = "execution_records"

    id = Column(String, primary_key=True)
    date = Column(String, nullable=False)
    business_line = Column(String, nullable=False)
    task_id = Column(String)
    title = Column(String)
    artifact_path = Column(String)
    word_count = Column(Integer, default=0)
    result = Column(String)
    result_detail = Column(String)
    cost_usd = Column(Float, default=0.0)
    model = Column(String)
    notes = Column(String)

    # Reserved: Anthropic 4-layer abstraction + approval gates
    session_id = Column(String)
    environment_id = Column(String)
    event_count = Column(Integer, default=0)
    requires_review = Column(Integer, default=0)
    review_status = Column(String)
    runtime_id = Column(String)

    # Data source tracking fields
    data_source = Column(String, default="mock")    # real/mock/derived/partial
    source_name = Column(String, default="seed")     # specific source identifier
    source_path = Column(String)                      # original file path
    sync_batch_id = Column(String)                    # batch identifier for refresh
    last_synced_at = Column(String)                   # ISO timestamp of sync

    created_at = Column(String)

__table_args__ = (
    Index("idx_exec_date", "date"),
    Index("idx_exec_business_line", "business_line"),
    Index("idx_exec_result", "result"),
)
