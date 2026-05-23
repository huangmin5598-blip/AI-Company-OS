# @PRODUCT Model — OS Core
from sqlalchemy import Column, String, Integer, Text
from app.models.base import Base

class CronJob(Base):
    __tablename__ = "cron_jobs"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    agent_id = Column(String)
    business_line_id = Column(String)
    schedule_expr = Column(String)
    timezone = Column(String, default="Asia/Shanghai")
    enabled = Column(Integer, default=0)
    last_run_at = Column(String)
    last_status = Column(String)
    last_duration_ms = Column(Integer, default=0)
    consecutive_errors = Column(Integer, default=0)
    last_error = Column(String)
    data_source = Column(String, default="mock")
    source_name = Column(String, default="seed")
    source_path = Column(String)
    sync_batch_id = Column(String)
    last_synced_at = Column(String)
    created_at = Column(String)
    updated_at = Column(String)
