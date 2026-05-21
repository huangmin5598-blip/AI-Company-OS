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


@router.get("/api/v1/costs/trend")
def get_cost_trend(days: int = Query(7, ge=1, le=90)):
    """Return daily cost time series. Grouped by agent_id if group_by_agent=true."""
    session = get_sync_session()
    try:
        from datetime import datetime, timedelta
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

        rows = session.query(
            CostSnapshot.date,
            CostSnapshot.agent_id,
            CostSnapshot.model,
            CostSnapshot.input_tokens,
            CostSnapshot.output_tokens,
            CostSnapshot.cost_usd,
        ).filter(CostSnapshot.created_at >= cutoff).all()

        # Aggregate by date
        daily_totals: dict[str, dict] = {}
        daily_by_agent: dict[str, dict[str, dict]] = {}

        for r in rows:
            d = r.date
            agent = r.agent_id or "unknown"

            # Total
            if d not in daily_totals:
                daily_totals[d] = {"cost": 0.0, "input_tokens": 0, "output_tokens": 0, "calls": 0}
            daily_totals[d]["cost"] += r.cost_usd or 0
            daily_totals[d]["input_tokens"] += r.input_tokens or 0
            daily_totals[d]["output_tokens"] += r.output_tokens or 0
            daily_totals[d]["calls"] += 1

            # By agent
            if d not in daily_by_agent:
                daily_by_agent[d] = {}
            if agent not in daily_by_agent[d]:
                daily_by_agent[d][agent] = {"cost": 0.0, "input_tokens": 0, "output_tokens": 0, "calls": 0}
            daily_by_agent[d][agent]["cost"] += r.cost_usd or 0
            daily_by_agent[d][agent]["input_tokens"] += r.input_tokens or 0
            daily_by_agent[d][agent]["output_tokens"] += r.output_tokens or 0
            daily_by_agent[d][agent]["calls"] += 1

        # Build sorted time series
        sorted_dates = sorted(set(list(daily_totals.keys()) + list(daily_by_agent.keys())))

        total_series = [
            {
                "date": d,
                "cost_usd": round(daily_totals.get(d, {}).get("cost", 0), 6),
                "input_tokens": daily_totals.get(d, {}).get("input_tokens", 0),
                "output_tokens": daily_totals.get(d, {}).get("output_tokens", 0),
                "calls": daily_totals.get(d, {}).get("calls", 0),
            }
            for d in sorted_dates
        ]

        agent_series = {}
        for d in sorted_dates:
            agents = daily_by_agent.get(d, {})
            for agent, stats in agents.items():
                if agent not in agent_series:
                    agent_series[agent] = []
                agent_series[agent].append({
                    "date": d,
                    "cost_usd": round(stats["cost"], 6),
                    "input_tokens": stats["input_tokens"],
                    "output_tokens": stats["output_tokens"],
                    "calls": stats["calls"],
                })

        return {
            "total": total_series,
            "by_agent": agent_series,
            "days": days,
        }
    finally:
        session.close()


@router.get("/api/v1/skills")
def get_skills_map():
    """Return company-wide skills coverage and gaps."""
    session = get_sync_session()
    try:
        from app.models.agent import Agent
        agents = session.query(Agent).all()

        # Collect all skills and which agents have them
        skill_coverage: dict[str, list[str]] = {}
        all_agent_skills: dict[str, list[str]] = {}

        for a in agents:
            if a.skills:
                try:
                    import json
                    skills = json.loads(a.skills)
                except (json.JSONDecodeError, TypeError):
                    skills = []
            else:
                skills = []
            all_agent_skills[a.id] = skills
            for s in skills:
                s_lower = s.lower().strip()
                if s_lower not in skill_coverage:
                    skill_coverage[s_lower] = []
                skill_coverage[s_lower].append(a.id)

        # Build skill items
        skill_items = []
        for skill, agent_ids in sorted(skill_coverage.items()):
            count = len(agent_ids)
            skill_items.append({
                "skill": skill,
                "agent_count": count,
                "agents": agent_ids,
                "coverage": "full" if count >= 2 else ("partial" if count == 1 else "gap"),
            })

        # Find gaps: tasks requesting skills no agent has
        from app.models.task import Task
        all_tasks = session.query(Task).all()
        task_skill_gaps: list[dict] = []
        for t in all_tasks:
            if t.required_skills:
                try:
                    import json
                    req_skills = json.loads(t.required_skills)
                except (json.JSONDecodeError, TypeError):
                    req_skills = []
                for rs in req_skills:
                    rs_lower = rs.lower().strip()
                    if rs_lower not in skill_coverage:
                        task_skill_gaps.append({
                            "skill": rs_lower,
                            "task_id": t.id,
                            "task_title": t.title[:60],
                        })

        return {
            "total_skills": len(skill_items),
            "total_agents_with_skills": sum(1 for s in all_agent_skills.values() if s),
            "skills": skill_items,
            "task_gaps": task_skill_gaps,
            "agent_skills": {k: v for k, v in all_agent_skills.items() if v},
        }
    finally:
        session.close()
