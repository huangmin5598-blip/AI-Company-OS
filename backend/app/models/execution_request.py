# @PRODUCT Model — OS Core
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.sql import func
from app.models.base import Base


class ExecutionRequest(Base):
    __tablename__ = "execution_requests"

    id = Column(Integer, primary_key=True)
    source_type = Column(String, nullable=False)
    # improvement_proposal / task / command
    source_id = Column(String, nullable=True)
    proposal_id = Column(Integer, unique=True, nullable=True)
    task_id = Column(Integer, nullable=True)
    runtime_id = Column(String, nullable=True)
    action_type = Column(String, nullable=False)
    # diagnose_task / create_retry_task / generate_memory_update_draft
    # run_status_check / run_dry_run_command
    action_payload_json = Column(Text, nullable=False, default='{}')
    risk_level = Column(String, nullable=False, default='low')
    dry_run_required = Column(Integer, default=0)
    dry_run_result_json = Column(Text, nullable=True)
    status = Column(String, nullable=False, default='draft')
    # draft → pending_confirmation → dry_run_completed (command only)
    # → approved_for_execute → executed
    # → verification_pending → verified_success / verified_failed
    # → cancelled
    execute_confirmed_by = Column(String, nullable=True)
    execute_confirmed_at = Column(DateTime, nullable=True)
    execute_confirmation_note = Column(Text, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    execution_result_json = Column(Text, nullable=True)
    verification_result_json = Column(Text, nullable=True)
    verified_by = Column(String, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
