# @PRODUCT Router — OS Core
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.database import get_sync_session
from app.models.goal_session import GoalSession
from app.schemas.goal_session import GoalSessionCreate, GoalSessionResponse

router = APIRouter(tags=["CEO Goal Sessions"])


@router.get("/api/v1/ceo/goal-sessions", response_model=list[GoalSessionResponse])
def list_goal_sessions(
    status: Optional[str] = Query(None),
    source_channel: Optional[str] = Query(None),
    business_line: Optional[str] = Query(None),
):
    session = get_sync_session()
    try:
        query = session.query(GoalSession)
        if status:
            query = query.filter(GoalSession.status == status)
        if source_channel:
            query = query.filter(GoalSession.source_channel == source_channel)
        if business_line:
            query = query.filter(GoalSession.business_line == business_line)
        sessions = query.order_by(GoalSession.created_at.desc()).all()
        return [_goal_session_to_response(s) for s in sessions]
    finally:
        session.close()


@router.post("/api/v1/ceo/goal-sessions", response_model=GoalSessionResponse, status_code=201)
def create_goal_session(body: GoalSessionCreate):
    session = get_sync_session()
    try:
        goal = GoalSession(
            source_channel=body.source_channel,
            raw_goal=body.raw_goal,
            client_request_id=body.client_request_id,
            interpreted_goal=body.interpreted_goal,
            goal_type=body.goal_type,
            business_line=body.business_line,
            priority=body.priority,
            risk_level=body.risk_level,
            status=body.status,
            decomposition_json=body.decomposition_json,
            task_ids_json=body.task_ids_json,
            approval_ids_json=body.approval_ids_json,
            model_used=body.model_used,
            confidence=body.confidence,
            schema_version=body.schema_version,
            error_message=body.error_message,
        )
        session.add(goal)
        session.commit()
        session.refresh(goal)
        return _goal_session_to_response(goal)
    finally:
        session.close()


@router.get("/api/v1/ceo/goal-sessions/{session_id}", response_model=GoalSessionResponse)
def get_goal_session(session_id: int):
    session = get_sync_session()
    try:
        goal = session.query(GoalSession).filter(GoalSession.id == session_id).first()
        if not goal:
            raise HTTPException(status_code=404, detail="Goal session not found")
        return _goal_session_to_response(goal)
    finally:
        session.close()


def _goal_session_to_response(g: GoalSession) -> GoalSessionResponse:
    return GoalSessionResponse(
        id=g.id,
        source_channel=g.source_channel or "cc_panel",
        raw_goal=g.raw_goal,
        client_request_id=g.client_request_id,
        interpreted_goal=g.interpreted_goal,
        goal_type=g.goal_type,
        business_line=g.business_line,
        priority=g.priority or "medium",
        risk_level=g.risk_level or "medium",
        status=g.status or "draft",
        decomposition_json=g.decomposition_json,
        task_ids_json=g.task_ids_json,
        approval_ids_json=g.approval_ids_json,
        model_used=g.model_used,
        confidence=g.confidence,
        schema_version=g.schema_version or "v0.3.0",
        error_message=g.error_message,
        created_at=g.created_at.isoformat() if g.created_at else None,
        updated_at=g.updated_at.isoformat() if g.updated_at else None,
    )
