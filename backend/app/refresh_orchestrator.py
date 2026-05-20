"""Refresh orchestrator — sync real OpenClaw data on demand."""
from datetime import datetime
from app.database import get_sync_session, init_db
from app.models.base import Base
from app.models.refresh_log import RefreshLog

def now():
    return datetime.utcnow().isoformat() + "Z"

def run_refresh() -> dict:
    """Run all OpenClaw adapters in sequence. Falls back to mock seed on failure."""
    from app.database import sync_engine
    from app.adapters import (
        sync_agents, sync_cron_jobs,
        sync_production_ledger, sync_artifact_ledger,
        sync_costs, sync_alerts, clear_resolved_alerts,
    )

    init_db()

    results = {}

    # 1. Agents — from openclaw CLI
    agent_result = sync_agents()
    results["agents"] = agent_result

    # 2. Cron Jobs — from jobs.json
    cron_result = sync_cron_jobs()
    results["cron_jobs"] = cron_result

    # 3. Execution Records — from production ledger
    ledger_result = sync_production_ledger()
    results["execution_records"] = ledger_result

    # 4. Artifacts — from artifact ledger
    artifact_result = sync_artifact_ledger()
    results["artifacts"] = artifact_result

    # 5. Costs — from gateway-lite
    cost_result = sync_costs()
    results["costs"] = cost_result

    # 6. Alerts — detect from errors
    alert_result = sync_alerts()
    results["alerts"] = alert_result

    # 7. Clear old resolved alerts
    clear_result = clear_resolved_alerts()
    results["resolved_alerts"] = clear_result

    # Log the refresh
    all_ok = all(
        r.get("status") == "ok"
        for r in results.values()
        if isinstance(r, dict)
    )

    session = get_sync_session()
    try:
        session.add(RefreshLog(
            refreshed_at=now(),
            status="ok" if all_ok else "partial",
            summary=str({k: v.get("records", v.get("new_alerts", 0)) for k, v in results.items() if isinstance(v, dict)}),
            created_at=now(),
        ))
        session.commit()
    finally:
        session.close()

    return results


def seed_mock_fallback():
    """Seed mock data only if agents table is empty (fallback when OpenClaw unavailable)."""
    from app.database import get_sync_session
    from app.models.agent import Agent

    session = get_sync_session()
    try:
        if session.query(Agent).count() > 0:
            return  # Already has data, don't overwrite with mock
    finally:
        session.close()

    # Only seed mock if no adapters have run yet
    from app.seed import seed_database
    seed_database()
