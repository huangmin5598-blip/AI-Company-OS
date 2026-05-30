# @PRODUCT Router — OS Core
"""Founder Console — aggregated system status for the Dashboard tab.

Single endpoint that returns everything Founder needs to know:
  - System health (summary)
  - Work Orders by status
  - Recent Run Ledger events
  - Recent assets
  - Open decisions / drafts
  - Capability Registry summary
  - Recommended actions
"""
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter
from sqlalchemy import text

from app.database import get_sync_session
from app.models.run_ledger_event import RunLedgerEvent
from app.models.asset_record import AssetRecord
from app.models.work_order import WorkOrder
from app.services.preflight_checks import run_all as run_preflight

router = APIRouter(prefix="/api/v1/founder-console", tags=["founder-console"])

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_BRIEFS_DIR = _PROJECT_ROOT / "reports" / "ceo-briefs"
_REVIEWS_DIR = _PROJECT_ROOT / "reports" / "ceo-brief-reviews"
_DECISION_LOG = _REVIEWS_DIR / "DECISION-LOG.md"
_DRAFTS_DIR = _PROJECT_ROOT / "reports" / "work-order-drafts"
_CAPABILITY_REGISTRY = _PROJECT_ROOT / "config" / "capability-registry.yaml"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


@router.get("")
def get_founder_console():
    """Aggregated system status for the Founder Dashboard."""
    session = get_sync_session()
    try:
        data = {
            "generated_at": _now(),
            "work_orders": _get_wo_summary(session),
            "recent_events": _get_recent_events(session),
            "recent_assets": _get_recent_assets(session),
            "latest_brief": _get_latest_brief(),
            "decisions": _get_decisions_summary(),
            "drafts": _get_drafts_summary(),
            "capabilities": _get_capability_summary(),
            "health_summary": _get_health_summary(),
            "recommended_actions": _get_recommended_actions(session),
        }
        return data
    finally:
        session.close()


@router.get("/health")
def get_preflight_health():
    """Run full preflight checks and return results."""
    return run_preflight()


def _get_wo_summary(session) -> dict:
    total = session.query(WorkOrder).count()
    by_status = {}
    for row in session.query(WorkOrder.status, text("COUNT(*) as cnt")).group_by(WorkOrder.status).all():
        by_status[row[0]] = row[1]

    recent_completed = session.query(WorkOrder).filter(
        WorkOrder.status == "completed"
    ).order_by(WorkOrder.completed_at.desc()).limit(3).all()

    return {
        "total": total,
        "by_status": by_status,
        "recent_completed": [
            {
                "id": wo.work_order_id,
                "status": wo.status,
                "summary": (wo.result_summary or "")[:80],
                "completed_at": str(wo.completed_at)[:19] if wo.completed_at else "",
            }
            for wo in recent_completed
        ],
    }


def _get_recent_events(session, limit: int = 10) -> list:
    events = session.query(RunLedgerEvent).order_by(
        RunLedgerEvent.timestamp.desc()
    ).limit(limit).all()

    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "source_id": e.source_id,
            "work_order_id": e.work_order_id,
            "decision_id": e.decision_id,
            "draft_id": e.draft_id,
            "asset_id": e.asset_id,
            "timestamp": e.timestamp,
            "summary": (e.summary or "")[:120],
        }
        for e in events
    ]


def _get_recent_assets(session, limit: int = 8) -> list:
    assets = session.query(AssetRecord).order_by(
        AssetRecord.created_at.desc()
    ).limit(limit).all()

    return [
        {
            "id": a.id,
            "asset_type": a.asset_type,
            "path": a.path,
            "summary": (a.summary or "")[:80],
            "source_work_order": a.source_work_order,
            "source_decision": a.source_decision,
            "created_at": a.created_at,
        }
        for a in assets
    ]


def _get_latest_brief() -> dict | None:
    if not _BRIEFS_DIR.exists():
        return None
    briefs = sorted([f for f in _BRIEFS_DIR.iterdir() if f.suffix == ".md" and "INDEX" not in f.name])
    if not briefs:
        return None
    latest = briefs[-1]
    return {
        "path": str(latest.relative_to(_PROJECT_ROOT)),
        "filename": latest.name,
        "exists": True,
    }


def _get_decisions_summary() -> dict:
    if not _DECISION_LOG.exists():
        return {"total": 0, "executed": 0, "pending": 0}

    with open(_DECISION_LOG, "r") as f:
        text_content = f.read()

    lines = text_content.strip().split("\n")
    decision_rows = [l for l in lines if l.startswith("|") and "DEC-" in l]
    executed = sum(1 for l in decision_rows if "Execution Completed" in l)
    return {
        "total": len(decision_rows),
        "executed": executed,
        "pending": len(decision_rows) - executed,
    }


def _get_drafts_summary() -> dict:
    if not _DRAFTS_DIR.exists():
        return {"total": 0, "pending": 0, "completed": 0}

    drafts = [f for f in _DRAFTS_DIR.iterdir() if f.name.startswith("WO-DRAFT-") and f.suffix == ".md"]
    pending = 0
    for d in drafts:
        content = d.read_text(encoding="utf-8")
        if "_draft_status: draft" in content or "_draft_status: created" in content:
            pending += 1

    return {
        "total": len(drafts),
        "pending": pending,
        "completed": len(drafts) - pending,
    }


def _get_capability_summary() -> dict:
    if not _CAPABILITY_REGISTRY.exists():
        return {"agents": 0, "loaded": False}

    try:
        import yaml
        with open(_CAPABILITY_REGISTRY, "r") as f:
            data = yaml.safe_load(f)
        agents = data.get("agents", [])
        return {
            "agents": len(agents),
            "loaded": True,
            "by_runtime": {
                agent.get("runtime", "unknown"): sum(
                    1 for a in agents if a.get("runtime", "") == agent.get("runtime", "")
                )
                for agent in agents
            } if agents else {},
        }
    except Exception:
        return {"agents": 0, "loaded": False, "error": "parse_error"}


def _get_health_summary() -> dict:
    """Basic health checks — expanded to full Preflight in Sprint C."""
    checks = []

    # DB — check if we can reach it (already proven by this API working)
    checks.append({"name": "Database", "status": "pass"})

    # Run Ledger writable
    session = get_sync_session()
    try:
        session.execute(text("SELECT 1 FROM run_ledger_events LIMIT 1"))
        checks.append({"name": "Run Ledger", "status": "pass"})
    except Exception:
        checks.append({"name": "Run Ledger", "status": "fail", "action": "Run DB migration (init_db)"})
    finally:
        session.close()

    # Asset Registry writable
    session = get_sync_session()
    try:
        session.execute(text("SELECT 1 FROM asset_registry LIMIT 1"))
        checks.append({"name": "Asset Registry", "status": "pass"})
    except Exception:
        checks.append({"name": "Asset Registry", "status": "fail", "action": "Run DB migration (init_db)"})
    finally:
        session.close()

    # Reports path writable
    briefs_ok = _BRIEFS_DIR.exists()
    checks.append({
        "name": "CEO Briefs",
        "status": "pass" if briefs_ok else "warning",
        "action": "Create reports/ceo-briefs/" if not briefs_ok else "",
    })

    # Capability Registry
    cap_ok = _CAPABILITY_REGISTRY.exists()
    checks.append({
        "name": "Capability Registry",
        "status": "pass" if cap_ok else "warning",
        "action": "Create config/capability-registry.yaml" if not cap_ok else "",
    })

    # Decision Log
    dec_ok = _DECISION_LOG.exists()
    checks.append({
        "name": "Decision Log",
        "status": "pass" if dec_ok else "info",
    })

    return {
        "checks": checks,
        "pass_count": sum(1 for c in checks if c["status"] == "pass"),
        "total": len(checks),
    }


def _get_recommended_actions(session) -> list:
    actions = []

    # Check for WO needs_review
    needs_review = session.query(WorkOrder).filter(WorkOrder.status == "needs_review").count()
    if needs_review > 0:
        actions.append({
            "priority": "high",
            "message": f"{needs_review} WO(s) need review",
            "command": "python3 scripts/work_order_control.py approve-dispatch <WO_ID>",
        })

    # Check for pending decisions
    dec = _get_decisions_summary()
    if dec.get("pending", 0) > 0:
        actions.append({
            "priority": "medium",
            "message": f"{dec['pending']} unexecuted decision(s)",
            "command": "python3 scripts/review_brief.py status",
        })

    # Check for pending drafts
    drafts = _get_drafts_summary()
    if drafts.get("pending", 0) > 0:
        actions.append({
            "priority": "medium",
            "message": f"{drafts['pending']} draft(s) pending Founder fill",
            "command": "python3 scripts/review_brief.py create-work-order <draft>",
        })

    return actions
