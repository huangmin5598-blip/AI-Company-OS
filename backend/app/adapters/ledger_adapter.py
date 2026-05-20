"""Adapter: sync execution records and artifacts from OpenClaw ledger files."""
import json
from datetime import datetime
from pathlib import Path
from app.database import get_sync_session
from app.models.execution_record import ExecutionRecord
from app.models.artifact import Artifact
from app.config import settings

def now():
    return datetime.utcnow().isoformat() + "Z"

def sync_production_ledger() -> dict:
    """Sync execution records from production-flow-ledger.json."""
    path = Path(settings.PRODUCTION_LEDGER_PATH).expanduser().resolve()
    if not path.exists():
        return {"status": "error", "error": f"File not found: {path}", "records": 0}

    session = get_sync_session()
    try:
        with open(path) as f:
            data = json.load(f)
        
        runs = data.get("runs", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        
        for r in runs:
            rid = r.get("runIntentId") or r.get("run_id", "")
            passed = r.get("validatorPassed", False)
            result = "passed" if passed else "pending"
            
            session.add(ExecutionRecord(
                id=rid,
                date=datetime.utcnow().strftime("%Y-%m-%d"),
                business_line="unknown",
                task_id=rid,
                title=r.get("artifactId", ""),
                result=result,
                word_count=r.get("wordCount", 0),
                cost_usd=r.get("costUsd", 0),
                model=r.get("model", ""),
                artifact_path=r.get("artifactId", ""),
                created_at=now(),
            ))
        
        session.commit()
        return {"status": "ok", "records": len(runs)}
    except Exception as e:
        session.rollback()
        return {"status": "error", "error": str(e), "records": 0}
    finally:
        session.close()


def sync_artifact_ledger() -> dict:
    """Sync artifacts from artifact-ledger.json."""
    path = Path(settings.ARTIFACT_LEDGER_PATH).expanduser().resolve()
    if not path.exists():
        return {"status": "error", "error": f"File not found: {path}", "records": 0}

    session = get_sync_session()
    try:
        with open(path) as f:
            data = json.load(f)
        
        artifacts_data = data if isinstance(data, list) else (list(data.values()) if isinstance(data, dict) else [])
        
        for a in artifacts_data:
            if isinstance(a, dict):
                session.add(Artifact(
                    id=a.get("id", a.get("artifactId", "")),
                    run_id=a.get("runId", a.get("run_id", "")),
                    business_line=a.get("businessLine", a.get("project", "unknown")),
                    date=a.get("date", datetime.utcnow().strftime("%Y-%m-%d")),
                    artifact_path=a.get("artifactPath", a.get("path", "")),
                    word_count=a.get("wordCount", 0),
                    file_size_bytes=a.get("fileSize", 0),
                    artifact_status=a.get("status", a.get("artifactStatus", "created")),
                    validator_passed=1 if a.get("validatorPassed") else 0,
                    cost_usd=a.get("costUsd", 0),
                    model=a.get("model", ""),
                    created_at=now(),
                ))
        
        session.commit()
        return {"status": "ok", "records": len(artifacts_data)}
    except Exception as e:
        session.rollback()
        return {"status": "error", "error": str(e), "records": 0}
    finally:
        session.close()
