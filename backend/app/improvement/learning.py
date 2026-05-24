# @PRODUCT Learning — OS Core
from app.models.learning_candidate import LearningCandidate


def create_success_candidate(session, proposal) -> LearningCandidate | None:
    """Create a LearningCandidate draft on closed_success.

    Only generates a draft — does NOT auto-create Knowledge Proposal or Org Memory.
    Founder must manually confirm via the existing v0.4 pipeline.
    """
    candidate = LearningCandidate(
        source_type="improvement_proposal",
        source_id=f"improvement_proposal:{proposal.id}",
        source_summary=proposal.summary or proposal.title,
        candidate_type="success_pattern",
        summary=(
            f"Improvement proposal '{proposal.title}' closed successfully. "
            f"Type: {proposal.proposal_type}."
        ),
        recommendation=proposal.action_plan_json,
        approval_status="pending_approval",
    )
    session.add(candidate)
    session.flush()
    return candidate


def create_failure_candidate(session, proposal) -> LearningCandidate | None:
    """Create a LearningCandidate draft on closed_failed (Sprint C optional).

    Only generates a draft — Founder must manually confirm.
    Type is failure_pattern / tool_gap / context_update.
    """
    candidate = LearningCandidate(
        source_type="improvement_proposal",
        source_id=f"improvement_proposal:{proposal.id}",
        source_summary=proposal.summary or proposal.title,
        candidate_type="failure_pattern",
        summary=(
            f"Improvement proposal '{proposal.title}' closed with failure. "
            f"Type: {proposal.proposal_type}. Consider updating context or Org Memory."
        ),
        recommendation=proposal.action_plan_json,
        approval_status="pending_approval",
    )
    session.add(candidate)
    session.flush()
    return candidate
