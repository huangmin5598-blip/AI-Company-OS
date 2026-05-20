from fastapi import APIRouter
from app.database import get_sync_session
from app.models.cron_job import CronJob
from app.schemas.cron_job import CronJobResponse

router = APIRouter(tags=["Cron Jobs"])

@router.get("/api/v1/cron-jobs", response_model=list[CronJobResponse])
def list_cron_jobs():
    session = get_sync_session()
    try:
        jobs = session.query(CronJob).order_by(CronJob.name).all()
        return [
            CronJobResponse(
                id=j.id, name=j.name, agent_id=j.agent_id,
                business_line_id=j.business_line_id, schedule_expr=j.schedule_expr,
                enabled=bool(j.enabled), last_run_at=j.last_run_at,
                last_status=j.last_status, consecutive_errors=j.consecutive_errors or 0,
                last_error=j.last_error,
            ) for j in jobs
        ]
    finally:
        session.close()
