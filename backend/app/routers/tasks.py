# @PRODUCT Router — OS Core
"""Tasks API — CRUD for tasks + task_messages."""
import json
from fastapi import APIRouter, Query, HTTPException, Header
from typing import Optional
from datetime import datetime

from app.database import get_sync_session
from app.models.task import Task, TaskMessage
from app.models.command_log import CommandLog
from app.config import settings
from app.schemas.task import (
    TaskCreate, TaskUpdate, TaskResponse,
    TaskMessageResponse,
)

router = APIRouter(tags=["Tasks"])


@router.get("/api/v1/tasks", response_model=list[TaskResponse])
def list_tasks(
    status: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
):
    session = get_sync_session()
    try:
        query = session.query(Task)
        if status:
            query = query.filter(Task.status == status)
        if agent_id:
            query = query.filter(Task.agent_id == agent_id)
        if priority:
            query = query.filter(Task.priority == priority)

        query = query.order_by(Task.created_at.desc()).offset(offset).limit(limit)
        return query.all()
    finally:
        session.close()


@router.get("/api/v1/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int):
    session = get_sync_session()
    try:
        task = session.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    finally:
        session.close()


@router.post("/api/v1/tasks", response_model=TaskResponse, status_code=201)
def create_task(
    body: TaskCreate,
    x_confirm: str = Header(default=""),
    mode: str = Query("dry-run"),
):
    """Create a new task.
    
    Alpha capability — requires ALLOW_ALPHA_WRITE=true for real execution.
    Default mode is 'dry-run' (returns analysis, no execution).
    """
    session = get_sync_session()
    try:
        # === Safety Gate ===
        is_execute = mode == "execute"

        if is_execute:
            if not settings.ALLOW_ALPHA_WRITE:
                session.add(CommandLog(
                    endpoint="/api/v1/tasks",
                    command_type="task_create",
                    mode="rejected",
                    payload=json.dumps(body.model_dump(exclude_none=True)),
                    risk_level="medium",
                    requires_confirmation=1,
                    confirmed=0,
                    status="rejected",
                    result_summary="ALLOW_ALPHA_WRITE=false — execution blocked",
                    created_at=datetime.utcnow().isoformat(),
                ))
                session.commit()
                raise HTTPException(
                    status_code=403,
                    detail="Task creation disabled. ALLOW_ALPHA_WRITE is false. Use mode=dry-run for preview."
                )

            if x_confirm.lower() != "yes":
                session.add(CommandLog(
                    endpoint="/api/v1/tasks",
                    command_type="task_create",
                    mode="pending_confirmation",
                    payload=json.dumps(body.model_dump(exclude_none=True)),
                    risk_level="medium",
                    requires_confirmation=1,
                    confirmed=0,
                    status="rejected",
                    result_summary="Missing X-Confirm: yes header",
                    created_at=datetime.utcnow().isoformat(),
                ))
                session.commit()
                raise HTTPException(
                    status_code=400,
                    detail="Task creation requires header 'X-Confirm: yes'. Use mode=dry-run to preview."
                )

        # Log the attempt
        cmd_log = CommandLog(
            endpoint="/api/v1/tasks",
            command_type="task_create",
            mode=mode,
            payload=json.dumps(body.model_dump(exclude_none=True)),
            risk_level="medium",
            requires_confirmation=1 if is_execute else 0,
            confirmed=1 if is_execute else 0,
            status="dry-run" if not is_execute else "pending",
            created_at=datetime.utcnow().isoformat(),
        )
        session.add(cmd_log)
        session.flush()

        # If dry-run, return preview without mutating
        if not is_execute:
            session.commit()
            raise HTTPException(
                status_code=200,
                detail={
                    "status": "dry-run",
                    "message": "[DRY-RUN] Task not created. Use mode=execute + header X-Confirm: yes to create.",
                    "task_preview": body.model_dump(exclude_none=True),
                }
            )

        # === REAL EXECUTION (only reached if ALLOW_ALPHA_WRITE=true + X-Confirm=yes) ===
        task = Task(
            title=body.title,
            description=body.description,
            agent_id=body.agent_id,
            priority=body.priority,
            source=body.source,
            required_skills=body.required_skills,
            success_criteria=body.success_criteria,
            status="pending",
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        return task
    finally:
        session.close()


@router.patch("/api/v1/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    body: TaskUpdate,
    x_confirm: str = Header(default=""),
    mode: str = Query("dry-run"),
):
    """Update an existing task's fields.
    
    Alpha capability — requires ALLOW_ALPHA_WRITE=true for real execution.
    Default mode is 'dry-run' (returns analysis, no execution).
    """
    session = get_sync_session()
    try:
        task = session.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # === Safety Gate ===
        is_execute = mode == "execute"
        update_data = body.model_dump(exclude_unset=True)

        if is_execute:
            if not settings.ALLOW_ALPHA_WRITE:
                session.add(CommandLog(
                    endpoint=f"/api/v1/tasks/{task_id}",
                    command_type="task_update",
                    mode="rejected",
                    payload=json.dumps(update_data),
                    risk_level="medium",
                    requires_confirmation=1,
                    confirmed=0,
                    status="rejected",
                    result_summary="ALLOW_ALPHA_WRITE=false — execution blocked",
                    created_at=datetime.utcnow().isoformat(),
                ))
                session.commit()
                raise HTTPException(
                    status_code=403,
                    detail="Task update disabled. ALLOW_ALPHA_WRITE is false. Use mode=dry-run for preview."
                )

            if x_confirm.lower() != "yes":
                session.add(CommandLog(
                    endpoint=f"/api/v1/tasks/{task_id}",
                    command_type="task_update",
                    mode="pending_confirmation",
                    payload=json.dumps(update_data),
                    risk_level="medium",
                    requires_confirmation=1,
                    confirmed=0,
                    status="rejected",
                    result_summary="Missing X-Confirm: yes header",
                    created_at=datetime.utcnow().isoformat(),
                ))
                session.commit()
                raise HTTPException(
                    status_code=400,
                    detail="Task update requires header 'X-Confirm: yes'. Use mode=dry-run to preview."
                )

        # Log the attempt
        cmd_log = CommandLog(
            endpoint=f"/api/v1/tasks/{task_id}",
            command_type="task_update",
            mode=mode,
            payload=json.dumps(update_data),
            risk_level="medium",
            requires_confirmation=1 if is_execute else 0,
            confirmed=1 if is_execute else 0,
            status="dry-run" if not is_execute else "pending",
            created_at=datetime.utcnow().isoformat(),
        )
        session.add(cmd_log)
        session.flush()

        # If dry-run, return preview without mutating
        if not is_execute:
            session.commit()
            raise HTTPException(
                status_code=200,
                detail={
                    "status": "dry-run",
                    "message": "[DRY-RUN] Task not updated. Use mode=execute + header X-Confirm: yes to apply changes.",
                    "task_id": task_id,
                    "update_preview": update_data,
                }
            )

        # === REAL EXECUTION (only reached if ALLOW_ALPHA_WRITE=true + X-Confirm=yes) ===
        for key, value in update_data.items():
            setattr(task, key, value)

        task.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(task)
        return task
    finally:
        session.close()


@router.post("/api/v1/tasks/{task_id}/cancel", response_model=TaskResponse)
def cancel_task(task_id: int):
    session = get_sync_session()
    try:
        task = session.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.status in ("completed", "failed", "cancelled"):
            raise HTTPException(status_code=400, detail=f"Task already {task.status}")

        task.status = "cancelled"
        task.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(task)
        return task
    finally:
        session.close()


@router.post("/api/v1/tasks/{task_id}/retry", response_model=TaskResponse)
def retry_task(task_id: int):
    """Clone a failed task and re-create it as a new pending task."""
    session = get_sync_session()
    try:
        original = session.query(Task).filter(Task.id == task_id).first()
        if not original:
            raise HTTPException(status_code=404, detail="Task not found")
        if original.status != "failed":
            raise HTTPException(status_code=400, detail="Only failed tasks can be retried")

        # Clone the task
        new_task = Task(
            title=original.title,
            description=original.description,
            agent_id=original.agent_id,
            priority=original.priority,
            source="retry",
            required_skills=original.required_skills,
            success_criteria=original.success_criteria,
            status="pending",
        )
        session.add(new_task)
        session.flush()  # get new_task.id

        # Add retry message
        session.add(TaskMessage(
            task_id=new_task.id,
            role="system",
            content=f'{{"action":"retry_of","original_task_id":{task_id}}}',
        ))

        session.commit()
        session.refresh(new_task)
        return new_task
    finally:
        session.close()


# ── Task Messages ──

@router.get("/api/v1/tasks/{task_id}/messages", response_model=list[TaskMessageResponse])
def list_task_messages(task_id: int):
    session = get_sync_session()
    try:
        task = session.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        messages = session.query(TaskMessage).filter(
            TaskMessage.task_id == task_id
        ).order_by(TaskMessage.created_at.asc()).all()
        return messages
    finally:
        session.close()
