"""Monitor Insights API — expose Monitor Agent findings."""
from fastapi import APIRouter, Query
from app.database import get_sync_session
from app.models.monitor import MonitorInsight

router = APIRouter(tags=["Monitor"])


@router.get("/api/v1/monitor/insights")
def get_insights(
    insight_type: str = Query(None, description="Filter by type: failure_cluster, skill_gap, stalled_task, cost_anomaly, improvement_suggestion"),
    severity: str = Query(None, description="Filter by severity: critical, warning, info"),
    status: str = Query("new", description="Filter by status: new, acknowledged, resolved, dismissed"),
    limit: int = Query(20, ge=1, le=100),
):
    """Get Monitor Agent insights."""
    session = get_sync_session()
    try:
        query = session.query(MonitorInsight)

        if insight_type:
            query = query.filter(MonitorInsight.insight_type == insight_type)
        if severity:
            query = query.filter(MonitorInsight.severity == severity)
        if status:
            query = query.filter(MonitorInsight.status == status)

        rows = query.order_by(MonitorInsight.created_at.desc()).limit(limit).all()

        return [{
            "id": r.id,
            "insight_type": r.insight_type,
            "title": r.title,
            "description": r.description,
            "severity": r.severity,
            "details": r.details,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        } for r in rows]

    finally:
        session.close()


@router.patch("/api/v1/monitor/insights/{insight_id}")
def update_insight_status(insight_id: int, status: str = Query(..., description="new, acknowledged, resolved, dismissed")):
    """Acknowledge or resolve an insight."""
    session = get_sync_session()
    try:
        insight = session.query(MonitorInsight).filter(MonitorInsight.id == insight_id).first()
        if not insight:
            return {"error": f"Insight {insight_id} not found"}, 404

        from datetime import datetime
        insight.status = status
        if status in ("resolved", "dismissed"):
            insight.resolved_at = datetime.utcnow()
        insight.updated_at = datetime.utcnow()
        session.commit()

        return {"status": "ok", "insight_id": insight_id, "new_status": status}

    finally:
        session.close()


@router.get("/api/v1/monitor/summary")
def get_monitor_summary():
    """Quick health summary for dashboard."""
    session = get_sync_session()
    try:
        counts = {}
        for row in session.query(
            MonitorInsight.severity,
            MonitorInsight.status,
        ).all():
            key = f"{row.severity}_{row.status}"
            counts[key] = counts.get(key, 0) + 1

        return {
            "critical_unresolved": counts.get("critical_new", 0) + counts.get("critical_acknowledged", 0),
            "warning_unresolved": counts.get("warning_new", 0) + counts.get("warning_acknowledged", 0),
            "info_unresolved": counts.get("info_new", 0) + counts.get("info_acknowledged", 0),
            "total_unresolved": sum(
                v for k, v in counts.items()
                if k.endswith("_new") or k.endswith("_acknowledged")
            ),
        }
    finally:
        session.close()
