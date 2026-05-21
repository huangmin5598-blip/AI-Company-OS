"""Command API — send instructions to agents + Agent PATCH for skills."""
import subprocess
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.database import get_sync_session
from app.config import settings
from app.models.task import Task, TaskMessage
from app.models.agent import Agent
from app.schemas.task import CommandRequest, CommandResponse, TaskResponse
from app.schemas.agent import AgentPatchRequest

router = APIRouter(tags=["Command"])


@router.post("/api/v1/command", response_model=CommandResponse)
def send_command(body: CommandRequest):
    """Send a natural-language instruction to an agent.

    Creates a Task record, attempts to spawn an OpenClaw session,
    and returns the task for tracking.
    """
    session = get_sync_session()
    try:
        # 1. Verify agent exists
        agent = session.query(Agent).filter(Agent.id == body.agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{body.agent_id}' not found")

        # 2. Create task
        task = Task(
            title=body.instruction[:100],  # Truncate for title
            description=body.instruction,
            agent_id=body.agent_id,
            priority=body.priority,
            source="command",
            required_skills=body.required_skills,
            success_criteria=body.success_criteria,
            status="in_progress",
        )
        session.add(task)
        session.flush()  # Get task.id

        # 3. Add user message
        msg = TaskMessage(
            task_id=task.id,
            role="user",
            content=body.instruction,
        )
        session.add(msg)

        # 4. Try to spawn OpenClaw session
        try:
            spawn_cmd = [
                "openclaw", "sessions", "spawn",
                "--agent", body.agent_id,
                "--task", body.instruction,
                "--json",
            ]
            result = subprocess.run(
                spawn_cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=settings.OPENCLAW_WORKSPACE,
            )

            if result.returncode == 0:
                # Parse spawn output
                spawn_data = json.loads(result.stdout)

                # Add system message with session info
                session.add(TaskMessage(
                    task_id=task.id,
                    role="system",
                    content=json.dumps({
                        "action": "session_spawned",
                        "session_id": spawn_data.get("session_id", "unknown"),
                        "output": spawn_data.get("output", ""),
                    }, ensure_ascii=False),
                ))

                task.result_summary = spawn_data.get("output", "")[:500]
                task.status = "completed"
            else:
                # CLI failed
                session.add(TaskMessage(
                    task_id=task.id,
                    role="system",
                    content=json.dumps({
                        "action": "session_failed",
                        "error": result.stderr[:500],
                    }, ensure_ascii=False),
                ))
                task.status = "failed"
                task.error_message = result.stderr[:500]
                task.failure_reason = "openclaw_cli_error"

        except FileNotFoundError:
            # openclaw CLI not available — mark as in_progress for manual handling
            session.add(TaskMessage(
                task_id=task.id,
                role="system",
                content=json.dumps({
                    "action": "cli_not_found",
                    "error": "openclaw CLI not found on PATH",
                }, ensure_ascii=False),
            ))
            # Keep as in_progress — user can check manually
            task.error_message = "openclaw CLI not found — task queued for manual dispatch"

        except subprocess.TimeoutExpired:
            session.add(TaskMessage(
                task_id=task.id,
                role="system",
                content=json.dumps({
                    "action": "session_timeout",
                    "error": "openclaw sessions spawn timed out after 30s",
                }, ensure_ascii=False),
            ))
            task.status = "in_progress"  # Might still be running
            task.error_message = "OpenClaw spawn timed out (30s) — check manually"

        except Exception as e:
            session.add(TaskMessage(
                task_id=task.id,
                role="system",
                content=json.dumps({
                    "action": "session_error",
                    "error": str(e)[:500],
                }, ensure_ascii=False),
            ))
            task.status = "failed"
            task.error_message = str(e)[:500]
            task.failure_reason = "unknown_error"

        session.commit()
        session.refresh(task)

        return CommandResponse(
            task=TaskResponse.model_validate(task),
            message=f"指令已发送至 Agent '{body.agent_id}'（Task #{task.id}）",
        )
    finally:
        session.close()


@router.patch("/api/v1/agents/{name}", response_model=dict)
def patch_agent(name: str, body: AgentPatchRequest):
    """Update an agent's skills, capabilities, role, or status."""
    session = get_sync_session()
    try:
        agent = session.query(Agent).filter(Agent.id == name).first()
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")

        update_data = body.model_dump(exclude_unset=True, exclude_none=True)
        for key, value in update_data.items():
            setattr(agent, key, value)

        agent.updated_at = datetime.utcnow().isoformat()
        session.commit()

        return {
            "status": "ok",
            "agent": name,
            "updated_fields": list(update_data.keys()),
        }
    finally:
        session.close()
