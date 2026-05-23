# @PRODUCT Router — OS Core
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.database import get_sync_session
from app.models.task_pool import TaskPool
from app.schemas.task_pool import TaskPoolCreate, TaskPoolUpdate, TaskPoolResponse

router = APIRouter(tags=["Task Pool"])


@router.get("/api/v1/task-pool", response_model=list[TaskPoolResponse])
def list_task_pool(
    status: Optional[str] = Query(None),
    business_line: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
):
    session = get_sync_session()
    try:
        query = session.query(TaskPool)
        if status:
            query = query.filter(TaskPool.status == status)
        if business_line:
            query = query.filter(TaskPool.business_line == business_line)
        if source:
            query = query.filter(TaskPool.source == source)
        if priority:
            query = query.filter(TaskPool.priority == priority)

        tasks = query.order_by(TaskPool.created_at.desc()).all()
        return [_task_to_response(t) for t in tasks]
    finally:
        session.close()


@router.post("/api/v1/task-pool", response_model=TaskPoolResponse, status_code=201)
def create_task_pool(body: TaskPoolCreate):
    session = get_sync_session()
    try:
        task = TaskPool(
            title=body.title,
            description=body.description,
            business_line=body.business_line,
            source=body.source,
            source_id=body.source_id,
            status=body.status,
            priority=body.priority,
            risk_level=body.risk_level,
            assigned_agent=body.assigned_agent,
            requires_approval=1 if body.requires_approval else 0,
            acceptance_criteria=body.acceptance_criteria,
            execution_runtime=body.execution_runtime,
            execution_mode=body.execution_mode,
            execution_workspace=body.execution_workspace,
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        return _task_to_response(task)
    finally:
        session.close()


@router.get("/api/v1/task-pool/{task_id}", response_model=TaskPoolResponse)
def get_task_pool(task_id: int):
    session = get_sync_session()
    try:
        task = session.query(TaskPool).filter(TaskPool.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return _task_to_response(task)
    finally:
        session.close()


@router.patch("/api/v1/task-pool/{task_id}", response_model=TaskPoolResponse)
def update_task_pool(task_id: int, body: TaskPoolUpdate):
    session = get_sync_session()
    try:
        task = session.query(TaskPool).filter(TaskPool.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        update_data = body.model_dump(exclude_unset=True)
        if "requires_approval" in update_data:
            update_data["requires_approval"] = 1 if update_data["requires_approval"] else 0

        for key, value in update_data.items():
            setattr(task, key, value)

        session.commit()
        session.refresh(task)
        return _task_to_response(task)
    finally:
        session.close()


def _task_to_response(t: TaskPool) -> TaskPoolResponse:
    return TaskPoolResponse(
        id=t.id,
        title=t.title,
        description=t.description,
        business_line=t.business_line,
        source=t.source,
        source_id=t.source_id,
        status=t.status,
        priority=t.priority,
        risk_level=t.risk_level,
        assigned_agent=t.assigned_agent,
        context_pack_id=t.context_pack_id,
        requires_approval=bool(t.requires_approval),
        acceptance_criteria=t.acceptance_criteria,
        result_summary=t.result_summary,
        error_message=t.error_message,
        cost_usd=t.cost_usd or 0.0,
        failure_reason=t.failure_reason,
        execution_runtime=t.execution_runtime,
        execution_mode=t.execution_mode,
        execution_workspace=t.execution_workspace,
        created_at=t.created_at.isoformat() if t.created_at else None,
        updated_at=t.updated_at.isoformat() if t.updated_at else None,
        completed_at=t.completed_at.isoformat() if t.completed_at else None,
    )
