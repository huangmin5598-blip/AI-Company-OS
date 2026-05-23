# @PRODUCT Adapter — OS Core
"""Adapter: sync execution records and artifacts from OpenClaw ledger files.

Real ledger schema (production-flow-ledger.json):
  runs[]:
    runIntentId: str          # unique run identifier
    artifactId: str           # artifact reference
    validatorPassed: bool     # pass/fail
    updatedAt: str            # ISO timestamp

Real artifact schema (artifact-ledger.json) — may be corrupted/irregular.
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from app.database import get_sync_session
from app.models.execution_record import ExecutionRecord
from app.models.artifact import Artifact
from app.config import settings

BATCH_ID = None  # Set once per refresh cycle

def now():
    return datetime.utcnow().isoformat() + "Z"

def get_batch_id():
    global BATCH_ID
    if BATCH_ID is None:
        BATCH_ID = f"sync-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
    return BATCH_ID


def sync_production_ledger() -> dict:
    """Sync execution records from production-flow-ledger.json.

    Real ledger schema: runs[] with {runIntentId, artifactId, validatorPassed, updatedAt}
    Maps to DB ExecutionRecord fields.
    """
    path = Path(settings.PRODUCTION_LEDGER_PATH).expanduser().resolve()
    if not path.exists():
        return {"status": "error", "error": f"File not found: {path}", "records": 0}

    session = get_sync_session()
    batch_id = get_batch_id()
    try:
        with open(path) as f:
            data = json.load(f)

        runs = data.get("runs", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        synced = 0

        for r in runs:
            if not isinstance(r, dict):
                continue

            run_id = r.get("runIntentId") or r.get("run_id", str(uuid.uuid4()))
            artifact_id = r.get("artifactId", "")
            passed = r.get("validatorPassed", False)
            updated = r.get("updatedAt", now())

            # Parse updatedAt to extract date
            try:
                dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                date_str = datetime.utcnow().strftime("%Y-%m-%d")

            result = "passed" if passed else ("failed" if passed is False else "pending")

            # Upsert: replace existing record with same ID
            existing = session.query(ExecutionRecord).filter(ExecutionRecord.id == run_id).first()
            if existing:
                session.delete(existing)
                session.flush()

            session.add(ExecutionRecord(
                id=run_id,
                date=date_str,
                business_line="openclaw",       # derived from ledger context
                task_id=run_id,
                title=artifact_id or run_id,
                artifact_path=artifact_id,
                word_count=0,                    # not available in this ledger schema
                result=result,
                result_detail=f"validatorPassed={passed}" if passed is not None else "",
                cost_usd=0.0,                    # not tracked per run in this ledger
                model="",
                notes="",
                data_source="real",
                source_name="production_ledger",
                source_path=str(path),
                sync_batch_id=batch_id,
                last_synced_at=now(),
                created_at=updated,
            ))
            synced += 1

        session.commit()
        return {"status": "ok", "records": synced}
    except json.JSONDecodeError as e:
        return {"status": "error", "error": f"JSON parse error: {e}", "records": 0}
    except Exception as e:
        session.rollback()
        return {"status": "error", "error": str(e), "records": 0}
    finally:
        session.close()


def sync_artifact_ledger() -> dict:
    """Sync artifacts from artifact-ledger.json.

    Handles JSON parse errors gracefully — generates an alert instead of failing.
    Does NOT modify the original OpenClaw file.
    """
    path = Path(settings.ARTIFACT_LEDGER_PATH).expanduser().resolve()
    if not path.exists():
        return {"status": "error", "error": f"File not found: {path}", "records": 0}

    session = get_sync_session()
    batch_id = get_batch_id()
    try:
        with open(path) as f:
            raw = f.read()

        # Attempt to parse — catch JSON errors
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            # Log the parse error, do NOT modify the original file
            from app.models.alert import Alert
            existing_alert = session.query(Alert).filter(
                Alert.source == "artifact_adapter",
                Alert.source_id == "artifact_ledger_parse_error",
                Alert.resolved == 0,
            ).first()
            if not existing_alert:
                session.add(Alert(
                    severity="error",
                    title="Artifact Ledger 解析失败",
                    description=f"artifact-ledger.json 在行 {e.lineno} 列 {e.colno} 解析失败: {e.msg}. 文件未自动修改，请联系检查原始文件格式。",
                    source="artifact_adapter",
                    source_id="artifact_ledger_parse_error",
                    data_source="real",
                    source_name="artifact_ledger",
                    source_path=str(path),
                    sync_batch_id=batch_id,
                    last_synced_at=now(),
                    resolved=0,
                    created_at=now(),
                ))
                session.commit()
            return {"status": "error", "error": f"JSON parse error: {e}", "records": 0}

        # Normalize to list
        artifacts_data = data if isinstance(data, list) else (
            list(data.values()) if isinstance(data, dict) else []
        )
        synced = 0

        for a in artifacts_data:
            if not isinstance(a, dict):
                continue

            aid = a.get("id") or a.get("artifactId") or str(uuid.uuid4())

            existing = session.query(Artifact).filter(Artifact.id == aid).first()
            if existing:
                session.delete(existing)
                session.flush()

            session.add(Artifact(
                id=aid,
                run_id=a.get("runId") or a.get("run_id", ""),
                business_line=a.get("businessLine") or a.get("project", "unknown"),
                date=a.get("date", datetime.utcnow().strftime("%Y-%m-%d")),
                artifact_path=a.get("artifactPath") or a.get("path", ""),
                word_count=a.get("wordCount", 0),
                file_size_bytes=a.get("fileSize", 0),
                file_type=a.get("fileType", ""),
                validator_passed=1 if a.get("validatorPassed") else 0,
                artifact_status=a.get("status") or a.get("artifactStatus", "created"),
                cost_usd=float(a.get("costUsd", 0)),
                model=a.get("model", ""),
                data_source="real",
                source_name="artifact_ledger",
                source_path=str(path),
                sync_batch_id=batch_id,
                last_synced_at=now(),
                created_at=now(),
            ))
            synced += 1

        session.commit()
        return {"status": "ok", "records": synced}
    except Exception as e:
        session.rollback()
        return {"status": "error", "error": str(e), "records": 0}
    finally:
        session.close()
