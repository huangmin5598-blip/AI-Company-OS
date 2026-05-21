from fastapi import APIRouter, Query
from typing import Optional
from app.database import get_sync_session
from app.models.execution_record import ExecutionRecord
from app.schemas.execution import ExecutionRecordResponse

router = APIRouter(tags=["Runs"])

@router.get("/api/v1/runs", response_model=list[ExecutionRecordResponse])
def list_runs(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    business_line: Optional[str] = Query(None),
    result: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    session = get_sync_session()
    try:
        query = session.query(ExecutionRecord).filter(ExecutionRecord.data_source != 'mock')
        if date_from:
            query = query.filter(ExecutionRecord.date >= date_from)
        if date_to:
            query = query.filter(ExecutionRecord.date <= date_to)
        if business_line:
            query = query.filter(ExecutionRecord.business_line == business_line)
        if result:
            query = query.filter(ExecutionRecord.result == result)
        records = query.order_by(ExecutionRecord.date.desc()).offset(offset).limit(limit).all()
        return [
            ExecutionRecordResponse(
                id=r.id, date=r.date, business_line=r.business_line,
                task_id=r.task_id, title=r.title, word_count=r.word_count or 0,
                result=r.result, result_detail=r.result_detail,
                cost_usd=round(r.cost_usd or 0, 6), model=r.model,
                artifact_path=r.artifact_path,
            ) for r in records
        ]
    finally:
        session.close()

@router.get("/api/v1/runs/{run_id}", response_model=ExecutionRecordResponse)
def get_run(run_id: str):
    session = get_sync_session()
    try:
        from fastapi import HTTPException
        r = session.query(ExecutionRecord).filter(ExecutionRecord.data_source != 'mock', ExecutionRecord.id == run_id).first()
        if not r:
            raise HTTPException(status_code=404, detail="Run not found")
        return ExecutionRecordResponse(
            id=r.id, date=r.date, business_line=r.business_line,
            task_id=r.task_id, title=r.title, word_count=r.word_count or 0,
            result=r.result, result_detail=r.result_detail,
            cost_usd=round(r.cost_usd or 0, 6), model=r.model,
            artifact_path=r.artifact_path,
        )
    finally:
        session.close()
