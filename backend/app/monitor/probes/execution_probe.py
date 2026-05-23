# @PRODUCT Probe — OS Core
from app.database import get_sync_session
from app.models.execution_record import ExecutionRecord


async def collect(config: dict) -> dict:
    """Check recent execution failure rate using result field."""
    lookback = config.get("analyzers", {}).get("error_rate", {}).get("lookback_runs", 20)

    session = get_sync_session()
    try:
        records = session.query(ExecutionRecord).order_by(
            ExecutionRecord.id.desc()
        ).limit(lookback).all()

        total = len(records)
        failed_results = ("failed", "timeout")
        failed = sum(1 for r in records if r.result in failed_results)
        failed_reasons = [r.result for r in records if r.result in failed_results][:5]

        return {
            "total_runs": total,
            "failed_count": failed,
            "failure_rate": round(failed / total, 3) if total else 0.0,
            "sample_failures": failed_reasons,
        }
    finally:
        session.close()
