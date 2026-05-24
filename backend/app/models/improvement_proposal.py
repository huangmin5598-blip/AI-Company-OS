# @PRODUCT Model — OS Core
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.sql import func
from app.models.base import Base


class ImprovementProposal(Base):
    __tablename__ = "improvement_proposals"

    id = Column(Integer, primary_key=True)
    source_finding_id = Column(String, nullable=True)
    source_finding_type = Column(String, nullable=False)
    # stuck_task / cost_spike / error_rate / runtime_health
    proposal_type = Column(String, nullable=False)
    # retry_task_proposal / context_update_proposal / budget_review_proposal
    # runtime_recovery_proposal / memory_update_proposal
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    rationale = Column(Text, nullable=True)
    action_plan_json = Column(Text, nullable=False, default='{}')
    risk_level = Column(String, nullable=False, default='medium')
    # low / medium / high
    business_line = Column(String, nullable=True)
    requires_command_center = Column(Integer, default=0)
    recommended_next_step = Column(String, nullable=True)
    status = Column(String, nullable=False, default='draft')
    # draft → proposed → approved → action_created
    # → closed_success / closed_failed / rejected / dismissed
    approval_id = Column(Integer, nullable=True)
    created_task_id = Column(Integer, nullable=True)
    command_draft_json = Column(Text, nullable=True)
    verification_plan_json = Column(Text, nullable=False, default='{}')
    verification_result_json = Column(Text, nullable=True)
    verified_by = Column(String, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
