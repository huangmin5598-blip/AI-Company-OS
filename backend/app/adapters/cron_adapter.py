"""Adapter: sync cron jobs from ~/.openclaw/cron/jobs.json."""
import json
from datetime import datetime
from pathlib import Path
from app.database import get_sync_session
from app.models.cron_job import CronJob
from app.config import settings
from app.adapters.ledger_adapter import get_batch_id

def now():
    return datetime.utcnow().isoformat() + "Z"

def parse_ms_timestamp(ms: int) -> str:
    """Convert millisecond timestamp to ISO string."""
    if not ms:
        return None
    from datetime import timezone
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()

def sync_cron_jobs() -> dict:
    """Sync cron jobs from OpenClaw jobs.json to SQLite."""
    path = Path(settings.OPENCLAW_CRON_JOBS_PATH).expanduser().resolve()
    if not path.exists():
        return {"status": "error", "error": f"File not found: {path}", "records": 0}
    
    session = get_sync_session()
    try:
        with open(path) as f:
            data = json.load(f)
        
        jobs = data.get("jobs", [])
        
        # Clear existing
        session.query(CronJob).delete()
        
        for j in jobs:
            job_id = j.get("id", "")
            name = j.get("name", "Unknown")
            agent_id = j.get("agentId", "")
            enabled = 1 if j.get("enabled", False) else 0
            schedule = j.get("schedule", {})
            expr = schedule.get("expr", "") if schedule else ""
            tz = schedule.get("tz", "Asia/Shanghai") if schedule else "Asia/Shanghai"
            
            state = j.get("state", {})
            if not state:
                state = {}
            
            last_run_ms = state.get("lastRunAtMs") or state.get("lastRunAtMs", 0)
            last_status = state.get("lastStatus", "unknown")
            last_duration = state.get("lastDurationMs", 0)
            consec_errors = state.get("consecutiveErrors", 0)
            last_error = state.get("lastError") or state.get("lastError", "")
            
            # Detect business_line_id from context
            bl_id = ""
            if name:
                name_lower = name.lower()
                if "小说" in name or "novel" in name_lower:
                    bl_id = "novel-v1"
                elif "内容" in name or "小红书" in name or "资讯" in name:
                    bl_id = "content-manager"
                elif "金融" in name or "a股" in name or "外围" in name or "finance" in name_lower:
                    bl_id = "finance-analyst"
                elif "亚马逊" in name or "选品" in name or "amazon" in name_lower:
                    bl_id = "amazon-seller"
                elif "研究" in name or "机会" in name or "research" in name_lower:
                    bl_id = "research-opportunity"
            
            session.add(CronJob(
                id=job_id,
                name=name,
                agent_id=agent_id,
                business_line_id=bl_id,
                schedule_expr=expr,
                timezone=tz,
                enabled=enabled,
                last_run_at=parse_ms_timestamp(last_run_ms),
                last_status=last_status,
                last_duration_ms=last_duration or 0,
                consecutive_errors=consec_errors or 0,
                last_error=last_error or None,
                data_source='real',
                source_name='cron_jobs_json',
                source_path=str(path),
                sync_batch_id=get_batch_id(),
                last_synced_at=now(),
                created_at=now(),
                updated_at=now(),
            ))
        
        session.commit()
        return {"status": "ok", "records": len(jobs)}
    except json.JSONDecodeError as e:
        return {"status": "error", "error": f"JSON parse error: {e}", "records": 0}
    except Exception as e:
        session.rollback()
        return {"status": "error", "error": str(e), "records": 0}
    finally:
        session.close()
