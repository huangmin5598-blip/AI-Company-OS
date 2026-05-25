# @PRODUCT Model — v0.9.1.1 Code Runtime Jobs
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.sql import func
from app.models.base import Base


class CodeRuntimeJob(Base):
    __tablename__ = "code_runtime_jobs"

    id = Column(Integer, primary_key=True)
    request_type = Column(String, nullable=False)
    # plan / patch / checks
    source_type = Column(String, nullable=False)
    # code_change_request / execution_request
    source_id = Column(Integer, nullable=True)
    # 关联的 CCR id 或 execution_request id
    runtime_id = Column(String, nullable=True)
    # codex / claude_code
    status = Column(String, nullable=False, default="queued")
    # queued → running → success / failed / timeout
    run_id = Column(String, nullable=True)
    # 对应 ~/.ai-company-os/codex-runs/{run_id}/
    run_stdout_path = Column(Text, nullable=True)
    run_stderr_path = Column(Text, nullable=True)
    result_text = Column(Text, nullable=True)
    # plan_summary / patch_diff / check_result
    error_text = Column(Text, nullable=True)
    elapsed_seconds = Column(Integer, nullable=True)
    exit_code = Column(Integer, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
