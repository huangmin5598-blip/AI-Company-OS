from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.database import get_sync_session
from app.models.ceo_action_log import CeoActionLog
from app.schemas.ceo_action_log import CeoActionLogCreate, CeoActionLogResponse

router = APIRouter(tags=["CEO Action Logs"])


@router.get("/api/v1/ceo/action-logs", response_model=list[CeoActionLogResponse])
def list_ceo_action_logs(
    intent_type: Optional[str] = Query(None),
    target_type: Optional[str] = Query(None),
    result_status: Optional[str] = Query(None),
):
    session = get_sync_session()
    try:
        query = session.query(CeoActionLog)
        if intent_type:
            query = query.filter(CeoActionLog.intent_type == intent_type)
        if target_type:
            query = query.filter(CeoActionLog.target_type == target_type)
        if result_status:
            query = query.filter(CeoActionLog.result_status == result_status)
        logs = query.order_by(CeoActionLog.created_at.desc()).all()
        return [_action_log_to_response(log) for log in logs]
    finally:
        session.close()


@router.post("/api/v1/ceo/action-logs", response_model=CeoActionLogResponse, status_code=201)
def create_ceo_action_log(body: CeoActionLogCreate):
    session = get_sync_session()
    try:
        log = CeoActionLog(
            source_channel=body.source_channel,
            raw_user_message=body.raw_user_message,
            intent_type=body.intent_type,
            target_type=body.target_type,
            target_id=body.target_id,
            action_taken=body.action_taken,
            payload_json=body.payload_json,
            result_status=body.result_status,
            result_summary=body.result_summary,
            confidence=body.confidence,
            requires_confirmation=1 if body.requires_confirmation else 0,
            confirmed_by_founder=1 if body.confirmed_by_founder else 0,
        )
        session.add(log)
        session.commit()
        session.refresh(log)
        return _action_log_to_response(log)
    finally:
        session.close()


def _action_log_to_response(log: CeoActionLog) -> CeoActionLogResponse:
    return CeoActionLogResponse(
        id=log.id,
        source_channel=log.source_channel or "cc_panel",
        raw_user_message=log.raw_user_message,
        intent_type=log.intent_type,
        target_type=log.target_type,
        target_id=log.target_id,
        action_taken=log.action_taken,
        payload_json=log.payload_json,
        result_status=log.result_status or "success",
        result_summary=log.result_summary,
        confidence=log.confidence,
        requires_confirmation=bool(log.requires_confirmation),
        confirmed_by_founder=bool(log.confirmed_by_founder),
        created_at=log.created_at.isoformat() if log.created_at else None,
    )
