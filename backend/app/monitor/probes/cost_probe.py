# @PRODUCT Probe — OS Core
from datetime import datetime, timedelta
from sqlalchemy import select, func as sa_func
from app.database import get_sync_session
from app.models.cost_snapshot import CostSnapshot


async def collect(config: dict) -> dict | None:
    """Compare recent cost vs historical average using SUM(cost_usd) delta."""
    lookback_hours = config.get("analyzers", {}).get("cost_spike", {}).get("lookback_hours", 24)

    now = datetime.utcnow()
    recent_start = now - timedelta(hours=lookback_hours)
    historical_start = now - timedelta(hours=lookback_hours * 2)

    session = get_sync_session()
    try:
        # SUM(cost_usd) per period — cost_snapshots has per-day cost_usd records
        recent = session.execute(
            select(sa_func.sum(CostSnapshot.cost_usd)).where(
                CostSnapshot.last_synced_at >= recent_start
            )
        ).scalar() or 0.0

        historical = session.execute(
            select(sa_func.sum(CostSnapshot.cost_usd)).where(
                CostSnapshot.last_synced_at >= historical_start,
                CostSnapshot.last_synced_at < recent_start
            )
        ).scalar() or 0.0

        multiplier = float(recent) / float(historical) if historical > 0 else 1.0

        return {
            "recent_period_cost": float(recent),
            "historical_period_cost": float(historical),
            "lookback_hours": lookback_hours,
            "multiplier": round(multiplier, 2),
        }
    finally:
        session.close()
