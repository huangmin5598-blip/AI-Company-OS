"""KnowledgeProposal model — semi-automated proposals from Learning Candidates."""
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.sql import func
from app.models.base import Base


class KnowledgeProposal(Base):
    __tablename__ = "knowledge_proposals"

    id = Column(Integer, primary_key=True)
    source_candidate_id = Column(Integer, nullable=False, unique=True)  # FK → learning_candidates.id, unique for idempotency
    proposal_type = Column(String, nullable=False)                       # failure_pattern / decision_pattern / tool_gap / context_update / sop_hint
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    structured_content = Column(Text, nullable=True)                     # JSON
    target_memory_type = Column(String, nullable=False)                  # failure_pattern / decision_pattern / tool_gap / context_update / sop_hint
    business_line = Column(String, nullable=True)
    status = Column(String, default="draft")                             # draft / committed / revised / rejected / expired
    org_memory_id = Column(Integer, nullable=True)                       # set when committed → FK org_memory.id
    committed_at = Column(DateTime, nullable=True)                       # set when committed
    founder_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
