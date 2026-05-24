# @PRODUCT Dry-run — OS Core
import json
from app.database import get_sync_session
from app.models.execution_request import ExecutionRequest


async def run_dry_run(execution_request_id: int) -> dict:
    """Run dry-run for command-type actions.

    Dry-run only generates text preview / checklist / manual instruction.
    Does NOT execute shell commands.
    Does NOT call subprocess.
    """
    session = get_sync_session()
    try:
        er = session.query(ExecutionRequest).filter_by(id=execution_request_id).first()
        if not er:
            raise ValueError(f"ExecutionRequest #{execution_request_id} not found")

        payload = json.loads(er.action_payload_json) if er.action_payload_json else {}

        # Generate preview only — no shell execution
        preview = {
            "action": er.action_type,
            "proposal_id": er.proposal_id,
            "preview": payload.get("steps", []),
            "note": "This is a dry-run preview. No shell command was executed. "
                    "Founder must execute any recovery commands manually.",
            "recommended_manual_steps": [
                "1. Review the preview above",
                "2. If the preview is acceptable, confirm execution",
                "3. Monitor the execution result after confirmation",
            ],
        }

        er.dry_run_result_json = json.dumps(preview, ensure_ascii=False)
        er.status = "dry_run_completed"
        session.commit()

        return preview
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
