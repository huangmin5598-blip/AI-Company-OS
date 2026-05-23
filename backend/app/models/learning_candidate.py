# @PRODUCT Model — OS Core
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.sql import func
from app.models.base import Base

class LearningCandidate(Base):
    __tablename__ = "learning_candidates"

    id = Column(Integer, primary_key=True)
    source_type = Column(String, nullable=False)    # failure / tool_gap / context_update / rule_update / asset_candidate
    source_id = Column(String, nullable=True)
    source_summary = Column(Text, nullable=True)
    candidate_type = Column(String, nullable=False) # failure_pattern / tool_gap / context_update / rule_update / sop_update / asset
    summary = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    approval_status = Column(String, default="pending_approval")
    # status: pending_approval / approved / rejected / approved_for_knowledge_update
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

# Generation rules (documentation, not enforced at model level):
# - Review = blocked or revision_required → auto-suggest creation (in alert-to-task logic)
# - Review = pass → no auto-generate, unless Founder manually creates asset_candidate
