# @PRODUCT Router — OS Core
from datetime import datetime
from fastapi import APIRouter
from app.database import get_sync_session
from app.models.refresh_log import RefreshLog
from app.schemas.refresh import RefreshResponse, RefreshStatusResponse

router = APIRouter(tags=["Refresh"])

@router.post("/api/v1/refresh", response_model=RefreshResponse)
def refresh_data():
    """Sync real OpenClaw data via adapters. Phase 3: live data from OpenClaw runtime."""
    from app.refresh_orchestrator import run_refresh
    results = run_refresh()

    refreshed_at = datetime.utcnow().isoformat() + "Z"
    summary = {}
    for k, v in results.items():
        if isinstance(v, dict):
            if "records_created" in v:
                summary[k] = v["records_created"]
            elif "records" in v:
                summary[k] = v["records"]
            else:
                summary[k] = v.get("new_alerts", v.get("resolved", 0))

    return RefreshResponse(
        status="ok",
        refreshed_at=refreshed_at,
        results=summary,
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
