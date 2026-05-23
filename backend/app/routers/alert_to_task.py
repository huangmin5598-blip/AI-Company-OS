# @PRODUCT Router — OS Core
"""Alert→Task auto-pooling router.

POST /api/v1/alert-to-task — manually or automatically triggers pooling
of unresolved alerts into the task_pool with context packs and approvals.
"""
import json
import logging
from fastapi import APIRouter
from app.database import get_sync_session
from app.models.alert import Alert
from app.models.task_pool import TaskPool
from app.models.context_pack import ContextPack
from app.models.approval import Approval

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Alert→Task"])


def _infer_business_line(source: str) -> str:
    """Map alert source to a business_line value."""
    src = (source or "").lower()
    if "amazon" in src:
        return "amazon"
    if "finance" in src or "金融" in src or "外围市场" in src:
        return "finance"
    if "novel" in src:
        return "novel"
    return "general"


def _infer_priority(severity: str) -> str:
    """Map alert severity to a priority."""
    sev = (severity or "").lower()
    if sev == "critical":
        return "critical"
    if sev == "error":
        return "high"
    return "medium"


def _infer_risk_level(severity: str) -> str:
    """Map alert severity to a risk_level.

    critical → high, error → high, warning/medium → medium.
    """
    sev = (severity or "").lower()
    if sev in ("critical", "error"):
        return "high"
    return "medium"


def _pool_unresolved_alerts() -> dict:
    """Core pooling logic — shared by the HTTP endpoint and cold start script.

    Uses a single session with savepoints per alert so that individual alert
    failures are rolled back independently without invalidating the session.

    Returns a summary dict with keys: pooled, skipped, errors.
    """
    session = get_sync_session()
    pooled = 0
    skipped = 0
    errors = []

    try:
        alerts = session.query(Alert).filter(Alert.resolved == 0).all()

        for alert in alerts:
            # Quick skip checks (no DB writes, no savepoint needed)
            if alert.resolved == 2:
                skipped += 1
                continue

            existing = session.query(TaskPool).filter(
                TaskPool.source == "alert",
                TaskPool.source_id == f"alert:{alert.id}",
            ).first()
            if existing is not None:
                skipped += 1
                continue

            # Use a savepoint so each alert's writes are independent
            try:
                with session.begin_nested():
                    # --- Map business line / priority / risk level ---
                    business_line = _infer_business_line(alert.source)
                    priority = _infer_priority(alert.severity)
                    risk_level = _infer_risk_level(alert.severity)

                    # --- Create TaskPool ---
                    task = TaskPool(
                        title=alert.title,
                        description=alert.description,
                        source="alert",
                        source_id=f"alert:{alert.id}",
                        business_line=business_line,
                        status="approval_required",
                        priority=priority,
                        risk_level=risk_level,
                        requires_approval=1,
                    )
                    session.add(task)
                    session.flush()  # populate task.id

                    # --- Create ContextPack ---
                    known_failures = alert.description
                    if known_failures and not known_failures.startswith("["):
                        known_failures = json.dumps([known_failures], ensure_ascii=False)

                    cp = ContextPack(
                        task_id=task.id,
                        founder_intent=f"修复{alert.title}，恢复正常执行",
                        known_failures=known_failures,
                        auto_generated=True,
                    )
                    session.add(cp)

                    # --- Create Approval ---
                    approval = Approval(
                        target_type="task",
                        target_id=task.id,
                        risk_level=risk_level,
                        reason=f"自动入池：{alert.title}",
                        status="approval_requested",
                    )
                    session.add(approval)

                    # --- Update alert ---
                    alert.resolved = 2

                # If we get here, the savepoint committed successfully
                pooled += 1

            except Exception as e:
                logger.exception("Failed to pool alert %s", alert.id)
                errors.append({"alert_id": alert.id, "reason": str(e)})

        # Commit the outer transaction (savepoints are already committed)
        session.commit()

    except Exception as e:
        session.rollback()
        logger.exception("Fatal error in _pool_unresolved_alerts")
        return {
            "pooled": 0,
            "skipped": 0,
            "errors": [{"alert_id": None, "reason": f"Fatal: {str(e)}"}],
        }
    finally:
        session.close()

    return {
        "pooled": pooled,
        "skipped": skipped,
        "errors": errors,
    }


@router.post("/api/v1/alert-to-task")
def trigger_alert_to_task():
    """Manual or automatic trigger to pool unresolved alerts into task_pool.

    Returns a summary:
      { pooled: int, skipped: int, errors: [{alert_id, reason}] }
    """
    return _pool_unresolved_alerts()
