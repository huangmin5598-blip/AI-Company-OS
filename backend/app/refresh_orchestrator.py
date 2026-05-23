# @PRODUCT Refresh orchestration — OS Core
"""Refresh orchestrator — sync real OpenClaw data on demand.

v0.1.1 changes:
- Clears old real data before each sync (prevents mock/real mixing)
- Sets sync_batch_id for traceability
- Falls back gracefully (keeps existing data on failure)
"""
from datetime import datetime
from app.database import get_sync_session, init_db
from app.models.refresh_log import RefreshLog
from app.models.execution_record import ExecutionRecord
from app.models.artifact import Artifact
from app.models.cost_snapshot import CostSnapshot
from app.models.alert import Alert
from app.adapters.ledger_adapter import get_batch_id

def now():
    return datetime.utcnow().isoformat() + "Z"

def run_refresh() -> dict:
    """Run all OpenClaw adapters in sequence.

    Strategy: clear old real data → sync fresh → keep mock fallback untouched.
    """
    from app.database import sync_engine
    from app.adapters import (
        sync_agents, sync_cron_jobs,
        sync_production_ledger, sync_artifact_ledger,
        sync_costs, sync_alerts, clear_resolved_alerts,
    )

    init_db()
    results = {}
    batch_id = get_batch_id()

    # 1. Agents — upsert (no clear needed, adapter handles it)
    agent_result = sync_agents()
    results["agents"] = agent_result

    # 2. Cron Jobs — upsert (no clear needed)
    cron_result = sync_cron_jobs()
    results["cron_jobs"] = cron_result

    # 3. Execution Records — clear old real data, then sync fresh
    _clear_old_real(ExecutionRecord, "execution_records")
    ledger_result = sync_production_ledger()
    results["execution_records"] = ledger_result

    # 4. Artifacts — clear old real data, then sync fresh
    _clear_old_real(Artifact, "artifacts")
    artifact_result = sync_artifact_ledger()
    results["artifacts"] = artifact_result

    # 5. Costs — clear old real+derived data, then sync fresh
    _clear_old_real(CostSnapshot, "cost_snapshots", include_derived=True)
    cost_result = sync_costs()
    results["costs"] = cost_result

    # 5b. Cost estimator — fill daily gaps from execution records
    from app.adapters.cost_estimator import estimate_costs
    estimate_result = estimate_costs()
    results["cost_estimator"] = estimate_result

    # 6. Alerts — clear old real alerts, then regenerate
    _clear_old_real(Alert, "alerts")
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
            batch_id=batch_id,
            status="ok" if all_ok else "partial",
            summary=str({k: v.get("records", v.get("new_alerts", v.get("resolved", 0))) for k, v in results.items() if isinstance(v, dict)}),
            created_at=now(),
        ))
        session.commit()
    finally:
        session.close()

    return results


def _clear_old_real(model_class, table_name: str, include_derived: bool = False):
    """Delete records where data_source='real' before re-syncing.
    
    Keeps mock/seed data intact.
    When include_derived=True, also clears data_source='derived' entries.
    """
    session = get_sync_session()
    try:
        from sqlalchemy import or_
        if include_derived:
            deleted = session.query(model_class).filter(
                or_(
                    model_class.data_source == "real",
                    model_class.data_source == "derived",
                )
            ).delete()
        else:
            deleted = session.query(model_class).filter(
                model_class.data_source == "real"
            ).delete()
        session.commit()
        if deleted > 0:
            print(f"[refresh] Cleared {deleted} old real records from {table_name}")
    except Exception as e:
        session.rollback()
        print(f"[refresh] Warning: could not clear {table_name}: {e}")
    finally:
        session.close()


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
