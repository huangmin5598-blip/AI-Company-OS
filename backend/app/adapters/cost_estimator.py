# @PRODUCT Adapter — OS Core
"""Cost estimation engine.

Generates derived daily cost data when real gateway-lite daily data is unavailable.
Distributes known aggregate costs across execution dates proportionally.

Data flow:
  aggregate costs (by-agent.json) × execution dates → derived daily costs
                                                    → data_source='derived'
                                                    → source_name='cost_estimator'
"""

import json
from datetime import datetime
from collections import defaultdict
from app.database import get_sync_session
from app.models.cost_snapshot import CostSnapshot
from app.models.execution_record import ExecutionRecord
from app.config import settings
from app.adapters.ledger_adapter import get_batch_id


def now():
    return datetime.utcnow().isoformat() + "Z"


def estimate_costs() -> dict:
    """Generate derived daily cost entries from aggregate costs and execution records."""
    session = get_sync_session()
    records_created = 0
    errors = []

    try:
        # 1. Read aggregate costs from cost-view files
        cost_by_agent = {}
        cost_view_dir = settings.GATEWAY_COST_DIR
        if not cost_view_dir:
            return {"status": "skipped", "reason": "GATEWAY_COST_DIR not configured"}

        from pathlib import Path
        cost_view_path = Path(cost_view_dir).expanduser().resolve()
        by_agent_path = cost_view_path / "by-agent.json"

        if not by_agent_path.exists():
            return {"status": "skipped", "reason": "by-agent.json not found"}

        with open(by_agent_path) as f:
            raw_agent_costs = json.load(f)

        for agent_id, info in raw_agent_costs.items():
            cost_by_agent[agent_id] = {
                "total_calls": info.get("total_calls", 0),
                "total_cost_usd": info.get("total_cost_usd", 0),
                "avg_cost_per_call": info.get("avg_cost_per_call", 0),
                "input_tokens": info.get("input_tokens", 0),
                "output_tokens": info.get("output_tokens", 0),
            }

        if not cost_by_agent:
            return {"status": "skipped", "reason": "no agent costs found"}

        # 2. Get existing daily cost dates (so we don't duplicate)
        existing_dates = set()
        existing = session.query(CostSnapshot.date).filter(
            CostSnapshot.data_source.in_(["real", "derived"])
        ).distinct().all()
        for (d,) in existing:
            existing_dates.add(d)

        # 3. Get execution record dates (real only)
        exec_records = session.query(
            ExecutionRecord.date,
        ).filter(
            ExecutionRecord.data_source == 'real'
        ).distinct().all()

        exec_dates = sorted(set(r.date for r in exec_records if r.date))
        if not exec_dates:
            return {"status": "skipped", "reason": "no real execution records found"}

        # Remove dates that already have data
        dates_to_fill = [d for d in exec_dates if d not in existing_dates]
        if not dates_to_fill:
            return {"status": "skipped", "reason": f"all execution dates already have cost data: {exec_dates}"}

        # 4. For each agent, distribute total cost across dates_to_fill
        batch_id = get_batch_id()

        for agent_id, cost_info in cost_by_agent.items():
            total_cost = cost_info["total_cost_usd"]
            avg_cost = cost_info["avg_cost_per_call"]
            total_calls = cost_info["total_calls"]
            total_input = cost_info["input_tokens"]
            total_output = cost_info["output_tokens"]

            if total_cost <= 0:
                continue

            num_dates = len(dates_to_fill)
            cost_per_date = round(total_cost / num_dates, 8) if num_dates > 0 else 0
            calls_per_date = max(1, round(total_calls / num_dates)) if num_dates > 0 else 0
            input_per_date = round(total_input / num_dates) if num_dates > 0 else 0
            output_per_date = round(total_output / num_dates) if num_dates > 0 else 0

            for date in dates_to_fill:
                session.add(CostSnapshot(
                    date=date,
                    agent_id=agent_id,
                    model="",
                    provider="",
                    input_tokens=input_per_date,
                    output_tokens=output_per_date,
                    cost_usd=cost_per_date,
                    fallback_count=0,
                    result_status="estimated",
                    task_hint=f"derived from by-agent.json avg",
                    created_at=now(),
                    data_source='derived',  # 👈 Not real, not mock — derived
                    source_name='cost_estimator',
                    source_path=str(by_agent_path),
                    sync_batch_id=batch_id,
                    last_synced_at=now(),
                ))
                records_created += 1

        # 5. Also add model-level estimates from by-model.json
        by_model_path = cost_view_path / "by-model.json"
        if by_model_path.exists():
            with open(by_model_path) as f:
                raw_model_costs = json.load(f)

            for model_name, info in raw_model_costs.items():
                total_cost = info.get("total_cost_usd", 0)
                if total_cost <= 0:
                    continue
                cost_per_date = round(total_cost / len(dates_to_fill), 8) if dates_to_fill else 0
                for date in dates_to_fill:
                    session.add(CostSnapshot(
                        date=date,
                        agent_id="",
                        model=model_name,
                        provider="",
                        input_tokens=0,
                        output_tokens=0,
                        cost_usd=cost_per_date,
                        fallback_count=0,
                        result_status="estimated",
                        task_hint=f"derived from by-model.json avg",
                        created_at=now(),
                        data_source='derived',
                        source_name='cost_estimator',
                        source_path=str(by_model_path),
                        sync_batch_id=batch_id,
                        last_synced_at=now(),
                    ))
                    records_created += 1

        session.commit()
        return {
            "status": "ok",
            "records_created": records_created,
            "dates_filled": dates_to_fill,
            "agents_used": list(cost_by_agent.keys()),
            "errors": errors[:3],
        }

    except Exception as e:
        session.rollback()
        return {"status": "error", "error": str(e), "records_created": records_created}
    finally:
        session.close()
