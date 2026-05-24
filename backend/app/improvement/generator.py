# @PRODUCT Generator — OS Core
import json
from app.database import get_sync_session
from app.models.improvement_proposal import ImprovementProposal
from app.models.approval import Approval


ACTIVE_STATUSES = {"proposed", "approved", "action_created"}

# Template-based proposal generation per finding type
PROPOSAL_TEMPLATES = {
    "stuck_task": {
        "proposal_type": "retry_task_proposal",
        "title_template": "Task \"{title}\" seems stuck — consider retry",
        "rationale": "Monitor detected task has not progressed beyond expected duration.",
        "action_plan": {
            "steps": [
                "1. Diagnose why task is stuck (context, dependencies, API status)",
                "2. Create a controlled retry entry (without auto-cancel)",
                "3. Monitor the retry result for first 5 minutes",
            ],
            "note": "v0.7 does NOT auto-cancel or auto-retry. This is a diagnostic entry.",
        },
        "verification_plan": {
            "checks": [
                "Check task status after retry — should transition to in_progress",
                "Check no duplicate running task",
                "Check execution_record created within 5 minutes",
            ],
            "expected": "Task transitions from stuck to in_progress",
        },
        "risk_level": "medium",
        "requires_command_center": False,
    },
    "cost_spike": {
        "proposal_type": "budget_review_proposal",
        "title_template": "Cost spike detected for {entity} — review budget",
        "rationale": "Cost monitor detected significant spike above threshold.",
        "action_plan": {
            "steps": [
                "1. Review cost trend for the affected agent or business line",
                "2. Consider lowering priority or setting budget cap",
                "3. Check for runaway loops or excessive retries",
            ],
        },
        "verification_plan": {
            "checks": [
                "Compare next 24h cost trend vs before spike",
                "Confirm alert does not repeat within 24h",
            ],
            "expected": "Cost returns to baseline within 24h",
        },
        "risk_level": "medium",
        "requires_command_center": False,
    },
    "runtime_health": {
        "proposal_type": "runtime_recovery_proposal",
        "title_template": "Runtime \"{name}\" is {status} — diagnose and recover",
        "rationale": "Runtime health check detected offline or degraded runtime.",
        "action_plan": {
            "steps": [
                "1. Check runtime health endpoint manually",
                "2. Inspect recent heartbeat history",
                "3. Attempt recovery via launchctl restart (only via Command Center)",
            ],
            "note": "v0.7 does NOT auto-restart. Recovery requires Command Center dry-run.",
        },
        "verification_plan": {
            "checks": [
                "Run runtime health check — should return online",
                "Confirm heartbeat status = online",
                "Confirm no new runtime_health finding in next scan",
            ],
            "expected": "Runtime status returns to online",
        },
        "risk_level": "high",
        "requires_command_center": True,
    },
    "error_rate": {
        "proposal_type": "memory_update_proposal",
        "title_template": "Error rate elevated for {entity} — consider knowledge update",
        "rationale": "Execution error rate exceeded threshold, suggesting knowledge gap.",
        "action_plan": {
            "steps": [
                "1. Analyze recent errors for common patterns",
                "2. Create Learning Candidate with failure patterns",
                "3. Update context or Org Memory to prevent recurrence",
            ],
        },
        "verification_plan": {
            "checks": [
                "Check error rate in next monitoring cycle",
                "Confirm error pattern is addressed in Org Memory",
            ],
            "expected": "Error rate returns below threshold",
        },
        "risk_level": "medium",
        "requires_command_center": False,
    },
}


def has_active_proposal(session, source_finding_id: str, proposal_type: str) -> bool:
    """Check if there's already an active proposal for this finding + type."""
    existing = session.query(ImprovementProposal).filter(
        ImprovementProposal.source_finding_id == source_finding_id,
        ImprovementProposal.proposal_type == proposal_type,
        ImprovementProposal.status.in_(ACTIVE_STATUSES),
    ).first()
    return existing is not None


def generate_proposal(finding: dict, config: dict) -> dict | None:
    """Generate an ImprovementProposal from a monitor finding.

    Returns dict with proposal data (not yet saved) or None if skipped.
    Each step is isolated — one failure doesn't block the caller.
    """
    try:
        return _do_generate(finding, config)
    except Exception:
        # Silently fail — generator should never crash the monitor runner
        return None


def _do_generate(finding: dict, config: dict) -> dict | None:
    # 1. Config filter
    imp_config = config.get("improvement_proposals", {})
    if not imp_config.get("enabled", True):
        return None

    min_severity = imp_config.get("min_severity", "warning")
    severity_order = {"info": 0, "warning": 1, "critical": 2}
    if severity_order.get(finding.get("severity", "info"), 0) < severity_order.get(min_severity, 1):
        return None  # Skip info-level findings

    finding_type = finding.get("finding_type", "")
    allowed_types = imp_config.get(
        "auto_generate_for",
        ["stuck_task", "cost_spike", "error_rate", "runtime_health"],
    )
    if finding_type not in allowed_types:
        return None

    # 2. Check template exists
    template = PROPOSAL_TEMPLATES.get(finding_type)
    if not template:
        return None

    source_finding_id = finding.get("source_id") or finding.get("id", "")

    session = get_sync_session()
    try:
        # 3. Dedup: same source_finding_id + proposal_type → only one active
        if has_active_proposal(session, source_finding_id, template["proposal_type"]):
            return None

        # 4. Build title from context
        context = finding.get("context", {})
        title = template["title_template"].format(**context)

        # 5. Create proposal (status = proposed)
        proposal = ImprovementProposal(
            source_finding_id=source_finding_id,
            source_finding_type=finding_type,
            proposal_type=template["proposal_type"],
            title=title,
            rationale=template.get("rationale", ""),
            action_plan_json=json.dumps(template["action_plan"], ensure_ascii=False),
            risk_level=template.get("risk_level", "medium"),
            requires_command_center=1 if template.get("requires_command_center") else 0,
            verification_plan_json=json.dumps(template["verification_plan"], ensure_ascii=False),
            status="proposed",
        )
        session.add(proposal)
        session.flush()

        # 6. Create approval record (sync: one transaction)
        approval = Approval(
            target_type="improvement_proposal",
            target_id=proposal.id,
            risk_level=proposal.risk_level,
            reason=proposal.rationale,
            status="approval_requested",
        )
        session.add(approval)
        session.flush()

        proposal.approval_id = approval.id
        session.commit()

        return {
            "id": proposal.id,
            "proposal_type": proposal.proposal_type,
            "title": proposal.title,
            "status": proposal.status,
            "approval_id": approval.id,
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
