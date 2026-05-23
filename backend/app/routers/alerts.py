# @PRODUCT Router — OS Core
from fastapi import APIRouter, Query
from typing import Optional
from app.database import get_sync_session
from app.models.alert import Alert
from app.schemas.alert import AlertResponse

router = APIRouter(tags=["Alerts"])

@router.get("/api/v1/alerts", response_model=list[AlertResponse])
def list_alerts(
    severity: Optional[str] = Query(None),
    resolved: Optional[bool] = Query(None),
):
    session = get_sync_session()
    try:
        query = session.query(Alert).filter(Alert.data_source != 'mock')
        if severity:
            query = query.filter(Alert.severity == severity)
        if resolved is not None:
            query = query.filter(Alert.resolved == (1 if resolved else 0))
        alerts = query.order_by(Alert.created_at.desc()).all()
        return [
            AlertResponse(
                id=a.id, severity=a.severity, title=a.title,
                description=a.description, source=a.source,
                resolved=bool(a.resolved), created_at=a.created_at,
            ) for a in alerts
        ]
    finally:
        session.close()
