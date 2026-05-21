"""Tasks API — CRUD for tasks + task_messages."""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime

from app.database import get_sync_session
from app.models.task import Task, TaskMessage
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
def create_task(body: TaskCreate):
    session = get_sync_session()
    try:
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
def update_task(task_id: int, body: TaskUpdate):
    session = get_sync_session()
    try:
        task = session.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        update_data = body.model_dump(exclude_unset=True)
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
