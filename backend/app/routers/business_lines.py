# @PRODUCT Router — OS Core
from fastapi import APIRouter, Query
from typing import Optional
from app.database import get_sync_session
from app.models.business_line import BusinessLine
from app.models.execution_record import ExecutionRecord
from app.schemas.business_line import BusinessLineResponse
from app.schemas.execution import ExecutionRecordResponse

router = APIRouter(tags=["Business Lines"])

@router.get("/api/v1/business-lines", response_model=list[BusinessLineResponse])
def list_business_lines():
    session = get_sync_session()
    try:
        lines = session.query(BusinessLine).all()
        result = []
        for l in lines:
            recent = session.query(ExecutionRecord).filter(
                ExecutionRecord.business_line == l.id
            ).order_by(ExecutionRecord.date.desc()).limit(3).all()
            artifacts = [r.title or r.task_id for r in recent if r.title or r.task_id]
            result.append(BusinessLineResponse(
                id=l.id, name=l.name, status=l.status,
                total_runs=l.total_runs or 0, failed_runs=l.failed_runs or 0,
                total_cost_usd=round(l.total_cost_usd or 0, 6),
                last_run_date=l.last_run_date, last_run_result=l.last_run_result,
                recent_artifacts=artifacts,
            ))
        return result
    finally:
        session.close()

@router.get("/api/v1/business-lines/{line_id}/runs", response_model=list[ExecutionRecordResponse])
def get_business_line_runs(line_id: str, limit: int = Query(20, ge=1, le=100)):
    session = get_sync_session()
    try:
        records = session.query(ExecutionRecord).filter(
            ExecutionRecord.business_line == line_id
        ).order_by(ExecutionRecord.date.desc()).limit(limit).all()
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
