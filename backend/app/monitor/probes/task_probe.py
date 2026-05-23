# @PRODUCT Probe — OS Core
from datetime import datetime, timedelta
from sqlalchemy import select
from app.database import get_sync_session
from app.models.task_pool import TaskPool

# Real statuses from task_pool.py
# draft → ready → approval_required → approved → running → review → done
MONITORABLE_STATUSES = {
    "running": 2,
    "approval_required": 4,
    "review": 4,
}


async def collect(config: dict) -> list[dict]:
    """Find tasks stuck beyond threshold per status."""
    results = []
    session = get_sync_session()
    try:
        for status, threshold_hours in MONITORABLE_STATUSES.items():
            cutoff = datetime.utcnow() - timedelta(hours=threshold_hours)
            rows = session.execute(
                select(TaskPool).where(
                    TaskPool.status == status,
                    TaskPool.updated_at < cutoff
                )
            ).scalars().all()

            for task in rows:
                hours = (datetime.utcnow() - task.updated_at).total_seconds() / 3600
                results.append({
                    "task_id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "threshold_hours": threshold_hours,
                    "hours_since_update": round(hours, 1),
                })
        return results
    finally:
        session.close()
