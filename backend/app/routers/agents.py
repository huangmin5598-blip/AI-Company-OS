from fastapi import APIRouter, Query
from typing import Optional
from app.database import get_sync_session
from app.models.agent import Agent
from app.models.execution_record import ExecutionRecord
from app.models.cost_snapshot import CostSnapshot
from app.schemas.agent import AgentResponse

router = APIRouter(tags=["Agents"])

@router.get("/api/v1/agents", response_model=list[AgentResponse])
def list_agents(status: Optional[str] = Query(None)):
    session = get_sync_session()
    try:
        query = session.query(Agent)
        if status:
            query = query.filter(Agent.status == status)
        agents = query.all()

        result = []
        for a in agents:
            runs = session.query(ExecutionRecord).filter(
                ExecutionRecord.business_line == a.name
            ).count()
            cost = session.query(CostSnapshot).filter(
                CostSnapshot.agent_id == a.name
            ).with_entities(
                CostSnapshot.cost_usd
            ).all()
            total_cost = sum(c[0] or 0 for c in cost)

            result.append(AgentResponse(
                id=a.id, name=a.name, identity=a.identity,
                workspace=a.workspace, model=a.model,
                routing_rules=a.routing_rules or 0,
                agent_type=a.agent_type or "openclaw",
                role=a.role,
                skills=a.skills,
                status=a.status or "offline",
                discovery_status=a.discovery_status or "discovered",
                activity_status=a.activity_status or "inactive",
                health_status=a.health_status or "ok",
                total_cost_usd=round(total_cost, 6),
                last_active_at=a.last_active_at,
                total_runs=runs,
            ))
        return result
    finally:
        session.close()

@router.get("/api/v1/agents/{name}", response_model=AgentResponse)
def get_agent(name: str):
    session = get_sync_session()
    try:
        a = session.query(Agent).filter(Agent.id == name).first()
        if not a:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Agent not found")

        runs = session.query(ExecutionRecord).filter(
            ExecutionRecord.business_line == a.name
        ).order_by(ExecutionRecord.date.desc()).limit(5).all()

        cost = session.query(CostSnapshot).filter(
            CostSnapshot.agent_id == a.name
        ).with_entities(
            CostSnapshot.cost_usd
        ).all()
        total_cost = sum(c[0] or 0 for c in cost)

        recent_task = runs[0].title if runs else None

        return AgentResponse(
            id=a.id, name=a.name, identity=a.identity,
            workspace=a.workspace, model=a.model,
            routing_rules=a.routing_rules or 0,
            agent_type=a.agent_type or "openclaw",
            role=a.role,
            skills=a.skills,
            status=a.status or "offline",
            discovery_status=a.discovery_status or "discovered",
            activity_status=a.activity_status or "inactive",
            health_status=a.health_status or "ok",
            total_cost_usd=round(total_cost, 6),
            last_active_at=a.last_active_at,
            total_runs=len(runs),
            recent_task=recent_task,
        )
    finally:
        session.close()
