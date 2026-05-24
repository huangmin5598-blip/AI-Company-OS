# @PRODUCT Policy — OS Core
from app.database import get_sync_session
from app.models.execution_request import ExecutionRequest
from app.models.ceo_action_log import CeoActionLog
from datetime import datetime


# ── Whitelist ──

SAFE_ACTIONS = {
    "diagnose_task",
    "create_retry_task",
    "generate_memory_update_draft",
    "run_status_check",
    "run_dry_run_command",
    # v0.9: code change actions (routed to Code-Capable Runtime Bridge)
    "code_change_request",
}

BLOCKED_ACTIONS = {
    "restart_runtime",
    "kill_agent",
    "cancel_task",
    "delete_file",
    "deploy",
    "change_budget_policy",
}

NON_DRY_RUN_ACTIONS = {
    "diagnose_task",
    "create_retry_task",
    "generate_memory_update_draft",
    "run_status_check",
}


# ── Validation ──


def validate_action(action_type: str) -> dict:
    """Validate action type against v0.8 whitelist.

    Blocked actions are never executed, even if Founder confirms.
    """
    if action_type in BLOCKED_ACTIONS:
        return {
            "allowed": False,
            "reason": f"'{action_type}' is not supported by v0.8 Controlled Execution Bridge. "
                      f"Founder must perform this action manually.",
        }
    if action_type not in SAFE_ACTIONS:
        return {
            "allowed": False,
            "reason": f"Unknown action type '{action_type}'. "
                      f"Must be one of: {', '.join(sorted(SAFE_ACTIONS))}",
        }
    return {"allowed": True, "action_type": action_type}


def log_blocked_action(action_type: str, proposal_id: int, reason: str):
    """Log blocked action to ceo_action_logs for audit trail."""
    session = get_sync_session()
    try:
        log = CeoActionLog(
            source_channel="execution_bridge",
            raw_user_message=f"Blocked action: {action_type} for proposal #{proposal_id}",
            intent_type="execution",
            target_type="improvement_proposal",
            target_id=proposal_id,
            action_taken="blocked",
            result_status="failed",
            result_summary=reason,
            requires_confirmation=False,
            confirmed_by_founder=False,
        )
        session.add(log)
        session.commit()
    finally:
        session.close()


def dry_run_required(action_type: str) -> bool:
    """Command-type actions need dry-run (text preview only, no shell)."""
    return action_type == "run_dry_run_command"


def has_active_request(session, proposal_id: int) -> ExecutionRequest | None:
    """Check if proposal already has an execution request (any status).

    DB UNIQUE constraint is the last line of defense;
    business layer checks first and returns existing request.
    """
    return session.query(ExecutionRequest).filter(
        ExecutionRequest.proposal_id == proposal_id,
    ).first()


VALID_TRANSITIONS = {
    "confirm": {"from": {"pending_confirmation"}, "to": "approved_for_execute"},
    "dry_run": {"from": {"pending_confirmation"}, "to": "dry_run_completed"},
    "execute": {"from": {"approved_for_execute"}, "to": "executed"},
    "verify": {"from": {"executed"}, "to": "verification_pending"},
    "cancel": {"from": {"pending_confirmation", "dry_run_completed"}, "to": "cancelled"},
}


def validate_transition(current_status: str, target_action: str) -> dict:
    """Validate state machine transitions."""
    rule = VALID_TRANSITIONS.get(target_action)
    if not rule:
        return {"allowed": False, "reason": f"Unknown transition '{target_action}'"}
    if current_status not in rule["from"]:
        return {
            "allowed": False,
            "reason": f"Cannot {target_action} from status '{current_status}'. "
                      f"Must be one of: {', '.join(sorted(rule['from']))}",
        }
    return {"allowed": True, "to": rule["to"]}
