# @PRODUCT Router — OS Core
import json
from datetime import datetime

from fastapi import APIRouter, HTTPException
from app.database import get_sync_session
from app.models.monitor_run import MonitorRun
from app.models.monitor_finding import MonitorFinding

router = APIRouter(prefix="/api/v1/monitor", tags=["monitor"])


# ── Serializers ──────────────────────────────
# Avoid SQLAlchemy __dict__ (_sa_instance_state pollution)


def _serialize_run(r: MonitorRun) -> dict:
    return {
        "id": r.id,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        "status": r.status,
        "summary": r.summary,
        "findings_count": r.findings_count,
        "alerts_created": r.alerts_created,
        "tasks_created": r.tasks_created,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _serialize_finding(f: MonitorFinding) -> dict:
    return {
        "id": f.id,
        "monitor_run_id": f.monitor_run_id,
        "finding_type": f.finding_type,
        "severity": f.severity,
        "title": f.title,
        "summary": f.summary,
        "evidence_json": json.loads(f.evidence_json) if f.evidence_json else None,
        "status": f.status,
        "source_id": f.source_id,
        "alert_id": f.alert_id,
        "task_id": f.task_id,
        "created_at": f.created_at.isoformat() if f.created_at else None,
    }


# POST /api/v1/monitor/run
@router.post("/run")
async def trigger_monitor_scan():
    from app.monitor.runner import run_monitor_scan
    result = await run_monitor_scan({})
    return result


# GET /api/v1/monitor/runs
@router.get("/runs")
async def list_runs(limit: int = 10, offset: int = 0):
    session = get_sync_session()
    try:
        runs = session.query(MonitorRun).order_by(
            MonitorRun.id.desc()
        ).offset(offset).limit(limit).all()
        return {"runs": [_serialize_run(r) for r in runs]}
    finally:
        session.close()


# GET /api/v1/monitor/runs/{run_id}
@router.get("/runs/{run_id}")
async def get_run(run_id: int):
    session = get_sync_session()
    try:
        run = session.query(MonitorRun).filter_by(id=run_id).first()
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        findings = session.query(MonitorFinding).filter_by(monitor_run_id=run_id).all()
        return {
            "run": _serialize_run(run),
            "findings": [_serialize_finding(f) for f in findings],
        }
    finally:
        session.close()


# GET /api/v1/monitor/findings
@router.get("/findings")
async def list_findings(
    status: str = None,
    severity: str = None,
    finding_type: str = None,
    limit: int = 20,
    offset: int = 0,
):
    session = get_sync_session()
    try:
        query = session.query(MonitorFinding)
        if status:
            query = query.filter_by(status=status)
        if severity:
            query = query.filter_by(severity=severity)
        if finding_type:
            query = query.filter_by(finding_type=finding_type)
        findings = query.order_by(MonitorFinding.id.desc()).offset(offset).limit(limit).all()
        return {"findings": [_serialize_finding(f) for f in findings], "total": query.count()}
    finally:
        session.close()


# GET /api/v1/monitor/findings/{finding_id}
@router.get("/findings/{finding_id}")
async def get_finding(finding_id: int):
    session = get_sync_session()
    try:
        finding = session.query(MonitorFinding).filter_by(id=finding_id).first()
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")
        return {"finding": _serialize_finding(finding)}
    finally:
        session.close()


# PATCH /api/v1/monitor/findings/{finding_id}/dismiss
@router.patch("/findings/{finding_id}/dismiss")
async def dismiss_finding(finding_id: int):
    session = get_sync_session()
    try:
        finding = session.query(MonitorFinding).filter_by(id=finding_id).first()
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")
        finding.status = "dismissed"
        session.commit()
        return {"status": "ok", "finding_id": finding_id}
    finally:
        session.close()


# POST /api/v1/monitor/findings/{finding_id}/create-task
@router.post("/findings/{finding_id}/create-task")
async def create_task_from_finding(finding_id: int):
    session = get_sync_session()
    try:
        finding = session.query(MonitorFinding).filter_by(id=finding_id).first()
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")
        if finding.status == "dismissed":
            raise HTTPException(status_code=400, detail="Finding already dismissed")

        from app.models.task_pool import TaskPool
        task = TaskPool(
            title=f"Investigate: {finding.title}",
            description=f"Monitor finding #{finding_id}: {finding.summary}",
            status="approval_required",
            source="monitor",
            source_id=f"monitor_finding:{finding_id}",
        )
        session.add(task)
        session.flush()
        finding.task_id = task.id
        finding.status = "converted"
        session.commit()
        return {"status": "ok", "task_id": task.id}
    finally:
        session.close()
