from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.database import get_sync_session
from app.models.agent import Agent
from app.models.business_line import BusinessLine
from app.models.execution_record import ExecutionRecord
from app.models.alert import Alert
from app.schemas.stats import StatsResponse

router = APIRouter(tags=["Stats"])

@router.get("/api/v1/stats", response_model=StatsResponse)
def get_stats():
    session = get_sync_session()
    try:
        agents = session.query(Agent).all()
        lines = session.query(BusinessLine).all()
        records = session.query(ExecutionRecord).filter(ExecutionRecord.data_source != 'mock').all()
        alerts = session.query(Alert).filter(Alert.data_source != 'mock', Alert.resolved == 0).all()

        online = sum(1 for a in agents if a.status == "online")
        busy = sum(1 for a in agents if a.status == "busy")
        offline = sum(1 for a in agents if a.status == "offline")
        running_lines = sum(1 for l in lines if l.status in ("guaranteed", "running"))
        error_lines = sum(1 for l in lines if l.status == "error")
        total_cost = sum(r.cost_usd or 0 for r in records)
        failed = sum(1 for r in records if r.result == "failed")

        return StatsResponse(
            agent_count=len(agents),
            online_agents=online,
            busy_agents=busy,
            offline_agents=offline,
            business_line_count=len(lines),
            running_lines=running_lines,
            error_lines=error_lines,
            month_cost_usd=round(total_cost, 6),
            total_executions=len(records),
            failed_executions=failed,
            pending_alerts=len(alerts),
        )
    finally:
        session.close()
