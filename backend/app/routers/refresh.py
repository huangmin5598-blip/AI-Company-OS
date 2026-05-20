from datetime import datetime
from fastapi import APIRouter
from app.database import get_sync_session
from app.models.refresh_log import RefreshLog
from app.schemas.refresh import RefreshResponse, RefreshStatusResponse

router = APIRouter(tags=["Refresh"])

@router.post("/api/v1/refresh", response_model=RefreshResponse)
def refresh_data():
    """Phase 1: Re-seed mock data. Phase 3: Connect real OpenClaw adapters."""
    from app.seed import clear_and_reseed
    results = clear_and_reseed()

    refreshed_at = datetime.utcnow().isoformat() + "Z"
    session = get_sync_session()
    try:
        session.add(RefreshLog(
            refreshed_at=refreshed_at, status="ok",
            summary=str(results),
            created_at=refreshed_at,
        ))
        session.commit()
    finally:
        session.close()

    return RefreshResponse(
        status="ok", refreshed_at=refreshed_at, results=results,
    )

@router.get("/api/v1/refresh/status", response_model=RefreshStatusResponse)
def refresh_status():
    session = get_sync_session()
    try:
        last = session.query(RefreshLog).order_by(RefreshLog.id.desc()).first()
        if last:
            return RefreshStatusResponse(
                last_refreshed_at=last.refreshed_at,
                status=last.status,
                summary=last.summary,
            )
        return RefreshStatusResponse()
    finally:
        session.close()
