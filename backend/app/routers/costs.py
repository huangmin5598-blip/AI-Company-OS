from fastapi import APIRouter, Query
from typing import Optional
from app.database import get_sync_session
from app.models.cost_snapshot import CostSnapshot
from app.schemas.cost import CostSummaryResponse, CostSummaryItem, DailyCostResponse

router = APIRouter(tags=["Costs"])

@router.get("/api/v1/costs", response_model=CostSummaryResponse)
def get_costs(group_by: str = Query("agent")):
    session = get_sync_session()
    try:
        rows = session.query(CostSnapshot).all()
        groups = {}
        for r in rows:
            key = getattr(r, group_by) if group_by in ("agent_id", "model", "provider") else r.agent_id
            if not key:
                key = "unknown"
            if key not in groups:
                groups[key] = {"total_calls": 0, "total_cost": 0.0}
            groups[key]["total_calls"] += 1
            groups[key]["total_cost"] += r.cost_usd or 0

        items = [
            CostSummaryItem(
                name=name, total_calls=stats["total_calls"],
                total_cost_usd=round(stats["total_cost"], 6),
                avg_cost_per_call=round(stats["total_cost"] / stats["total_calls"], 8) if stats["total_calls"] > 0 else 0,
            ) for name, stats in sorted(groups.items(), key=lambda x: -x[1]["total_cost"])
        ]
        return CostSummaryResponse(group=group_by, items=items)
    finally:
        session.close()

@router.get("/api/v1/costs/daily", response_model=DailyCostResponse)
def get_daily_costs(date: Optional[str] = Query(None)):
    session = get_sync_session()
    try:
        query = session.query(CostSnapshot)
        if date:
            query = query.filter(CostSnapshot.date == date)
        else:
            latest = query.order_by(CostSnapshot.date.desc()).first()
            if latest:
                query = session.query(CostSnapshot).filter(CostSnapshot.date == latest.date)
        rows = query.all()
        entry_date = rows[0].date if rows else "unknown"
        entries = [
            {"agent_id": r.agent_id, "model": r.model, "provider": r.provider,
             "input_tokens": r.input_tokens, "output_tokens": r.output_tokens,
             "cost_usd": round(r.cost_usd or 0, 6), "result_status": r.result_status,
             "task_hint": r.task_hint}
            for r in rows
        ]
        return DailyCostResponse(date=entry_date, entries=entries)
    finally:
        session.close()
