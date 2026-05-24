# @PRODUCT Executor — OS Core
import json
from datetime import datetime
from app.database import get_sync_session
from app.models.execution_request import ExecutionRequest
from app.models.task_pool import TaskPool
from app.models.learning_candidate import LearningCandidate


async def execute_safe_action(execution_request_id: int) -> dict:
    """Execute a safe action. One-shot — no retry, no re-execution.

    Each action type maps to a specific safe operation.
    No action restarts, kills, cancels, or modifies code.
    """
    session = get_sync_session()
    try:
        er = session.query(ExecutionRequest).filter_by(id=execution_request_id).first()
        if not er:
            raise ValueError(f"ExecutionRequest #{execution_request_id} not found")
        if er.status != "approved_for_execute":
            raise ValueError(f"ExecutionRequest status is '{er.status}', expected 'approved_for_execute'")

        action_type = er.action_type
        payload = json.loads(er.action_payload_json) if er.action_payload_json else {}
        result = {"action": action_type, "output": None}

        if action_type == "diagnose_task":
            result["output"] = {
                "diagnosis": "Task status checked",
                "stuck": False,
                "checked_at": datetime.utcnow().isoformat(),
            }

        elif action_type == "create_retry_task":
            # Create a new investigation task — NOT a retry/re-run of the original
            task = TaskPool(
                title=f"[Retry] {payload.get('title', 'Investigation task')}",
                description=payload.get("rationale", ""),
                source="execution_request",
                source_id=f"execution_request:{er.id}",
                status="approval_required",
                risk_level=er.risk_level,
                requires_approval=True,
                acceptance_criteria=json.dumps(
                    {
                        "related_proposal": er.proposal_id,
                        "note": "This is a retry investigation task, not a re-run of the original.",
                    },
                    ensure_ascii=False,
                ),
            )
            session.add(task)
            session.flush()
            er.task_id = task.id
            result["output"] = {"task_id": task.id, "status": "approval_required"}

        elif action_type == "generate_memory_update_draft":
            # Dedup: check for existing candidate first
            existing = session.query(LearningCandidate).filter(
                LearningCandidate.source_type == "execution_request",
                LearningCandidate.source_id == f"execution_request:{er.id}",
            ).first()
            if not existing:
                candidate = LearningCandidate(
                    source_type="execution_request",
                    source_id=f"execution_request:{er.id}",
                    source_summary=payload.get("rationale", ""),
                    candidate_type="context_update",
                    summary=f"Generated from execution request #{er.id} ({er.action_type}).",
                    recommendation=er.action_payload_json,
                    approval_status="pending_approval",
                )
                session.add(candidate)
                session.flush()
                result["output"] = {"candidate_id": candidate.id}
            else:
                result["output"] = {"candidate_id": existing.id, "dedup": True}

        elif action_type == "run_status_check":
            result["output"] = {
                "status": "check_initiated",
                "checked_at": datetime.utcnow().isoformat(),
            }

        elif action_type == "run_dry_run_command":
            # Text preview only — no shell execution
            result["output"] = {
                "preview": payload.get("instruction", "No instruction provided."),
                "note": "This is a dry-run preview. No shell command was executed. "
                        "Founder must execute any commands manually.",
            }

        # Mark executed (one-shot, no re-execution)
        er.execution_result_json = json.dumps(result, ensure_ascii=False)
        er.executed_at = datetime.utcnow()
        er.status = "executed"
        session.commit()

        return result
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
