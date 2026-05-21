"""Command API — send instructions to agents + Agent PATCH for skills."""
import subprocess
import json
import threading
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException
from app.database import get_sync_session
from app.config import settings
from app.models.task import Task, TaskMessage
from app.models.agent import Agent
from app.schemas.task import CommandRequest, CommandResponse, TaskResponse
from app.schemas.agent import AgentPatchRequest

router = APIRouter(tags=["Command"])


# Mapping: agent_id from dashboard -> OpenClaw agent name
# OpenClaw agent names have dashes; dashboard stores them with dashes too.
# If they differ in future, this mapping table grows.
AGENT_NAME_OVERRIDES = {
    "main": "main",
}


def _get_agent_cli_name(agent_id: str) -> str:
    """Resolve dashboard agent_id to OpenClaw agent CLI name."""
    return AGENT_NAME_OVERRIDES.get(agent_id, agent_id)


def _run_openclaw_task(
    task_id: int,
    agent_cli_name: str,
    instruction: str,
    workspace: str,
):
    """Run openclaw agent in a background thread. Updates task on completion."""
    session = get_sync_session()
    try:
        # Build the real OpenClaw command
        # Escape instruction so it's safe as a -m argument
        cmd = [
            "openclaw", "agent",
            "--agent", agent_cli_name,
            "-m", instruction,
            "--json",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 min max for real agent work
            cwd=workspace if workspace and Path(workspace).exists() else None,
        )

        task = session.query(Task).filter(Task.id == task_id).first()
        if not task:
            return  # task deleted while running

        if result.returncode == 0 and result.stdout.strip():
            try:
                data = json.loads(result.stdout)

                # Extract response text
                agent_reply = ""
                payloads = data.get("result", {}).get("payloads", [])
                if payloads:
                    texts = [p.get("text", "") for p in payloads if p.get("text")]
                    agent_reply = "\n".join(texts)

                # Extract usage metadata
                usage = {}
                agent_meta = data.get("result", {}).get("meta", {}).get("agentMeta", {})
                if agent_meta:
                    usage = {
                        "session_id": agent_meta.get("sessionId", ""),
                        "run_id": data.get("runId", ""),
                        "provider": agent_meta.get("provider", ""),
                        "model": agent_meta.get("model", ""),
                        "token_usage": agent_meta.get("usage", {}),
                        "duration_ms": data.get("result", {}).get("meta", {}).get("durationMs", 0),
                    }

                # Write agent response message
                session.add(TaskMessage(
                    task_id=task.id,
                    role="agent",
                    content=agent_reply[:5000] if agent_reply else "(no text response)",
                    msg_metadata=json.dumps(usage, ensure_ascii=False),
                ))

                task.result_summary = agent_reply[:500] if agent_reply else ""
                task.status = "completed" if data.get("summary") == "completed" else "failed"

                # Calculate cost from token usage
                tok = usage.get("token_usage", {})
                if tok:
                    total_tokens = tok.get("total", 0)
                    # Rough estimate: $0.002 per 1K tokens for MiniMax
                    task.cost_usd = round(total_tokens * 0.002 / 1000, 6)

            except json.JSONDecodeError:
                # CLI said ok but output isn't parseable JSON
                session.add(TaskMessage(
                    task_id=task.id,
                    role="system",
                    content=json.dumps({
                        "action": "parse_error",
                        "raw_stdout": result.stdout[:2000],
                    }, ensure_ascii=False),
                ))
                task.status = "failed"
                task.error_message = "Failed to parse OpenClaw output"
                task.failure_reason = "output_parse_error"

        elif result.returncode != 0:
            # CLI error
            # Try to parse stderr as JSON (OpenClaw errors are sometimes JSON)
            error_detail = result.stderr[:1000].strip()
            try:
                err_json = json.loads(result.stderr)
                error_detail = err_json.get("error", error_detail)
            except (json.JSONDecodeError, ValueError):
                pass

            session.add(TaskMessage(
                task_id=task.id,
                role="system",
                content=json.dumps({
                    "action": "execution_failed",
                    "error": error_detail,
                    "return_code": result.returncode,
                }, ensure_ascii=False),
            ))
            task.status = "failed"
            task.error_message = error_detail
            task.failure_reason = "openclaw_error"

        else:
            # Empty stdout
            session.add(TaskMessage(
                task_id=task.id,
                role="system",
                content=json.dumps({
                    "action": "empty_output",
                }, ensure_ascii=False),
            ))
            task.status = "failed"
            task.error_message = "OpenClaw returned empty output"
            task.failure_reason = "empty_output"

        task.updated_at = datetime.utcnow()
        session.commit()

    except subprocess.TimeoutExpired:
        session.add(TaskMessage(
            task_id=task_id,
            role="system",
            content=json.dumps({
                "action": "timeout",
                "error": "OpenClaw agent timed out after 600s",
            }, ensure_ascii=False),
        ))
        task = session.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = "failed"
            task.error_message = "OpenClaw agent timed out (600s)"
            task.failure_reason = "timeout"
            task.updated_at = datetime.utcnow()
            session.commit()

    except FileNotFoundError:
        session.add(TaskMessage(
            task_id=task_id,
            role="system",
            content=json.dumps({
                "action": "cli_not_found",
                "error": "openclaw CLI not found on PATH",
            }, ensure_ascii=False),
        ))
        task = session.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = "failed"
            task.error_message = "openclaw CLI not found on PATH"
            task.failure_reason = "cli_not_found"
            task.updated_at = datetime.utcnow()
            session.commit()

    except Exception as e:
        session.add(TaskMessage(
            task_id=task_id,
            role="system",
            content=json.dumps({
                "action": "unexpected_error",
                "error": str(e)[:500],
            }, ensure_ascii=False),
        ))
        task = session.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = "failed"
            task.error_message = str(e)[:500]
            task.failure_reason = "unexpected_error"
            task.updated_at = datetime.utcnow()
            session.commit()

    finally:
        session.close()


@router.post("/api/v1/command", response_model=CommandResponse)
def send_command(body: CommandRequest):
    """Send a natural-language instruction to an agent.

    Creates a Task record, dispatches to OpenClaw in background,
    and returns immediately for the frontend to poll.
    """
    session = get_sync_session()
    try:
        # 1. Verify agent exists
        agent = session.query(Agent).filter(Agent.id == body.agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{body.agent_id}' not found")

        # 2. Create task (pending, not executed yet)
        task = Task(
            title=body.instruction[:100],
            description=body.instruction,
            agent_id=body.agent_id,
            priority=body.priority,
            source="command",
            required_skills=body.required_skills,
            success_criteria=body.success_criteria,
            status="in_progress",  # Will be in_progress until background thread completes
        )
        session.add(task)
        session.flush()

        # 3. Add user message
        session.add(TaskMessage(
            task_id=task.id,
            role="user",
            content=body.instruction,
        ))

        # 4. Add system message noting dispatch
        agent_cli_name = _get_agent_cli_name(body.agent_id)
        session.add(TaskMessage(
            task_id=task.id,
            role="system",
            content=json.dumps({
                "action": "dispatched",
                "agent_cli": agent_cli_name,
                "command": f"openclaw agent --agent {agent_cli_name} -m \"{body.instruction[:80]}...\" --json",
            }, ensure_ascii=False),
        ))

        session.commit()
        session.refresh(task)

        # 5. Launch background thread for real OpenClaw execution
        workspace = agent.workspace if agent.workspace else settings.OPENCLAW_WORKSPACE
        thread = threading.Thread(
            target=_run_openclaw_task,
            args=(task.id, agent_cli_name, body.instruction, workspace),
            daemon=True,
        )
        thread.start()

        return CommandResponse(
            task=TaskResponse.model_validate(task),
            message=f"🚀 指令已派发至 Agent '{body.agent_id}'（Task #{task.id}），正在执行中...",
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
