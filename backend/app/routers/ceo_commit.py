# @PRODUCT Router — OS Core
import json
from fastapi import APIRouter, HTTPException
from app.database import get_sync_session
from app.models.goal_session import GoalSession
from app.models.ceo_action_log import CeoActionLog
from app.models.task_pool import TaskPool
from app.models.context_pack import ContextPack
from app.models.approval import Approval
from app.schemas.decomposition import CommitDecompositionRequest, CommitDecompositionResponse

router = APIRouter(tags=["CEO Commit Decomposition"])


@router.post("/api/v1/ceo/commit-decomposition", response_model=CommitDecompositionResponse)
def commit_decomposition(body: CommitDecompositionRequest):
    session = get_sync_session()
    try:
        # Idempotency check
        if body.client_request_id:
            existing = session.query(GoalSession).filter(
                GoalSession.client_request_id == body.client_request_id
            ).first()
            if existing:
                task_ids = json.loads(existing.task_ids_json) if existing.task_ids_json else []
                approval_ids = json.loads(existing.approval_ids_json) if existing.approval_ids_json else []
                return CommitDecompositionResponse(
                    goal_session_id=existing.id,
                    task_ids=task_ids,
                    approval_ids=approval_ids,
                    status=existing.status or "committed",
                )

        # Use savepoint for atomic transaction
        savepoint = session.begin_nested()

        try:
            # 1. Create GoalSession
            goal = GoalSession(
                source_channel=body.source_channel,
                raw_goal=body.raw_goal,
                client_request_id=body.client_request_id,
                interpreted_goal=body.interpreted_goal,
                goal_type=body.goal_type,
                business_line=body.business_line,
                risk_level=body.risk_level,
                priority=body.priority,
                status="committed",
                model_used=body.model_used,
                confidence=body.confidence,
                schema_version="v0.3.0",
            )
            session.add(goal)
            session.flush()  # Get goal.id

            task_ids = []
            approval_ids = []

            # 2. Create TaskPool + ContextPack + Approval for each task
            for task in body.tasks:
                # a. Create TaskPool
                tp = TaskPool(
                    title=task.title,
                    description=task.why,
                    source="ceo_goal",
                    source_id=f"goal_session:{goal.id}",
                    status="approval_required",
                    risk_level=task.risk_level,
                    priority=task.priority,
                    assigned_agent=task.assigned_agent,
                    acceptance_criteria=task.acceptance_criteria,
                    requires_approval=1,
                )
                session.add(tp)
                session.flush()  # Get tp.id
                task_ids.append(tp.id)

                # b. Create ContextPack
                cp = ContextPack(
                    task_id=tp.id,
                    auto_generated=True,
                )
                if task.context_pack:
                    cp.founder_intent = task.context_pack.founder_intent
                    if task.context_pack.related_sources:
                        cp.related_runs = json.dumps(task.context_pack.related_sources)
                    if task.context_pack.known_failures:
                        cp.known_failures = json.dumps(task.context_pack.known_failures)
                    if task.context_pack.constraints:
                        cp.constraints = task.context_pack.constraints
                session.add(cp)

                # c. Create Approval
                approval = Approval(
                    target_type="task",
                    target_id=tp.id,
                    risk_level=task.risk_level,
                    status="approval_requested",
                )
                session.add(approval)
                session.flush()  # Get approval.id
                approval_ids.append(approval.id)

            # 3. Update GoalSession with task_ids_json and approval_ids_json
            goal.task_ids_json = json.dumps(task_ids)
            goal.approval_ids_json = json.dumps(approval_ids)

            # 4. Create CeoActionLog
            action_log = CeoActionLog(
                source_channel=body.source_channel,
                raw_user_message=body.raw_goal,
                intent_type="goal_intake",
                target_type="goal_session",
                target_id=goal.id,
                action_taken="decomposed",
                payload_json=body.model_dump_json(),
                result_status="success",
                result_summary=f"Goal decomposed into {len(body.tasks)} tasks",
                confidence=body.confidence,
                requires_confirmation=0,
                confirmed_by_founder=0,
            )
            session.add(action_log)

            # 5. Commit the savepoint
            savepoint.commit()
            # Commit the outer session
            session.commit()

            return CommitDecompositionResponse(
                goal_session_id=goal.id,
                task_ids=task_ids,
                approval_ids=approval_ids,
                status="committed",
            )

        except Exception:
            savepoint.rollback()
            raise

    except HTTPException:
        raise
    except Exception as e:
        # On error, write a failed action log
        try:
            error_log = CeoActionLog(
                source_channel=body.source_channel,
                raw_user_message=body.raw_goal,
                intent_type="goal_intake",
                target_type="goal_session",
                action_taken="decomposed",
                result_status="failed",
                result_summary=str(e),
            )
            session.add(error_log)
            session.commit()
        except Exception:
            session.rollback()
        raise HTTPException(status_code=500, detail=f"Commit decomposition failed: {str(e)}")
    finally:
        session.close()
