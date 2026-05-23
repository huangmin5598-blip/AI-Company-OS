# @PRODUCT Adapter — OS Core
"""Adapter: detect alerts from cron job errors and execution failures."""
from datetime import datetime
from app.database import get_sync_session
from app.models.cron_job import CronJob
from app.models.execution_record import ExecutionRecord
from app.models.alert import Alert
from app.adapters.ledger_adapter import get_batch_id

def now():
    return datetime.utcnow().isoformat() + "Z"

def sync_alerts() -> dict:
    """Detect and create alerts from cron job errors and execution failures."""
    session = get_sync_session()
    try:
        new_alerts = 0
        existing_titles = {a.title for a in session.query(Alert).filter(Alert.resolved == 0).all()}
        
        # 1. Check cron jobs with errors
        error_jobs = session.query(CronJob).filter(
            CronJob.last_status == "error"
        ).all()
        
        for job in error_jobs:
            title = f"{job.name} 执行失败"
            if title not in existing_titles:
                desc = job.last_error or "未知错误"
                if job.consecutive_errors and job.consecutive_errors > 1:
                    desc = f"已连续报错 {job.consecutive_errors} 次: {desc}"
                
                session.add(Alert(
                    severity="error" if (job.consecutive_errors or 0) >= 2 else "warning",
                    title=title,
                    description=desc,
                    source=f"cron:{job.name}",
                    source_id=job.id,
                    resolved=0,
                    created_at=now(),
                    data_source='real',
                    source_name='alert_detector',
                    source_path='',
                    sync_batch_id=get_batch_id(),
                    last_synced_at=now(),
                ))
                new_alerts += 1
                existing_titles.add(title)
        
        # 2. Check execution records with failures
        failed_runs = session.query(ExecutionRecord).filter(
            ExecutionRecord.result == "failed"
        ).all()
        
        for run in failed_runs:
            title = f"{run.business_line} 执行失败 ({run.date})"
            if title not in existing_titles:
                session.add(Alert(
                    severity="warning",
                    title=title,
                    description=run.result_detail or f"业务线 {run.business_line} 在 {run.date} 执行失败",
                    source=f"execution:{run.business_line}",
                    source_id=run.id,
                    resolved=0,
                    created_at=now(),
                    data_source='real',
                    source_name='alert_detector',
                    source_path='',
                    sync_batch_id=get_batch_id(),
                    last_synced_at=now(),
                ))
                new_alerts += 1
                existing_titles.add(title)
        
        session.commit()
        return {"status": "ok", "new_alerts": new_alerts}
    except Exception as e:
        session.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        session.close()


def clear_resolved_alerts() -> dict:
    """Mark alerts as resolved if their source issue no longer exists."""
    session = get_sync_session()
    try:
        # Check if errored cron jobs are now OK
        unresolved = session.query(Alert).filter(Alert.resolved == 0).all()
        resolved_count = 0
        
        for alert in unresolved:
            if alert.source and alert.source.startswith("cron:"):
                job_name = alert.source.replace("cron:", "")
                # Check if this cron job is now ok
                job = session.query(CronJob).filter(
                    CronJob.name == job_name,
                    CronJob.last_status == "ok"
                ).first()
                if job:
                    alert.resolved = 1
                    resolved_count += 1
            
            elif alert.source and alert.source.startswith("execution:"):
                bl = alert.source.replace("execution:", "")
                # Check if there are recent successful runs
                recent_pass = session.query(ExecutionRecord).filter(
                    ExecutionRecord.business_line == bl,
                    ExecutionRecord.result == "passed"
                ).first()
                if recent_pass:
                    alert.resolved = 1
                    resolved_count += 1
        
        session.commit()
        return {"status": "ok", "resolved": resolved_count}
    except Exception as e:
        session.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        session.close()
