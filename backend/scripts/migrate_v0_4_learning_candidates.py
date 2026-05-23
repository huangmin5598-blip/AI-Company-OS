# @PLATFORM Migration script
"""Migration script: generate Knowledge Proposals from existing approved Learning Candidates.

Usage:
    cd backend && python scripts/migrate_v0_4_learning_candidates.py

This script finds all learning_candidates with approval_status='approved' and generates
a Knowledge Proposal (draft) for each, if one doesn't already exist.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import get_sync_session
from app.models.learning_candidate import LearningCandidate
from app.models.knowledge_proposal import KnowledgeProposal
from app.models.org_memory import OrgMemory
from sqlalchemy import select


CANDIDATE_TYPE_MAP = {
    "failure_pattern": "failure_pattern",
    "tool_gap": "tool_gap",
    "context_update": "context_update",
    "rule_update": "sop_hint",
    "sop_update": "sop_hint",
    "asset_candidate": "context_update",
}


def migrate():
    session = get_sync_session()
    try:
        # Find all approved learning candidates
        result = session.execute(
            select(LearningCandidate).where(
                LearningCandidate.approval_status.in_(
                    ["approved", "approved_for_knowledge_update"]
                )
            )
        )
        candidates = result.scalars().all()
        print(f"Found {len(candidates)} approved learning candidates.")

        created = 0
        skipped = 0
        for c in candidates:
            # Check if proposal already exists
            existing = session.execute(
                select(KnowledgeProposal).where(
                    KnowledgeProposal.source_candidate_id == c.id
                )
            ).scalar_one_or_none()
            if existing:
                print(f"  ⏭️ Candidate #{c.id} → proposal #{existing.id} (already exists)")
                skipped += 1
                continue

            target_type = CANDIDATE_TYPE_MAP.get(c.candidate_type, "context_update")
            title = c.summary or c.source_summary or f"Memory from Candidate #{c.id}"
            if len(title) > 200:
                title = title[:197] + "..."

            proposal = KnowledgeProposal(
                source_candidate_id=c.id,
                proposal_type=target_type,
                title=title,
                summary=c.summary,
                structured_content=c.recommendation,
                target_memory_type=target_type,
                status="draft",
            )
            session.add(proposal)
            session.flush()
            print(f"  ✅ Candidate #{c.id} → Proposal #{proposal.id} (draft, {target_type})")
            created += 1

        session.commit()
        print(f"\nDone: {created} created, {skipped} skipped.")
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    migrate()
