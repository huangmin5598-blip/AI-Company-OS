"""Adapter: sync agents from OpenClaw workspace + CLI.

Two data sources:
1. Directory scan (~/.openclaw/agents/) → discovery_status='discovered'
2. CLI (openclaw agents list) → discovery_status='registered'

Activity and health are computed cross-referencing execution_records, subagents/runs, and cron_jobs.
"""
import subprocess
import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from app.database import get_sync_session
from app.models.agent import Agent
from app.models.execution_record import ExecutionRecord
from app.models.cron_job import CronJob
from app.config import settings

def now():
    return datetime.utcnow().isoformat() + "Z"

def scan_agent_directories() -> set[str]:
    """Scan ~/.openclaw/agents/ for discovered agent directories."""
    agents_dir = Path(settings.OPENCLAW_AGENTS_DIR).expanduser().resolve()
    discovered = set()
    if agents_dir.exists():
        for entry in agents_dir.iterdir():
            if entry.is_dir() and not entry.name.startswith("."):
                discovered.add(entry.name)
    return discovered


def parse_agents_list(output: str) -> list[dict]:
    """Parse `openclaw agents list` CLI text output into structured records."""
    agents = []
    current = None

    for line in output.split("\n"):
        line = line.rstrip()
        m = re.match(r"^- ([\w][\w-]*)\s*(?:\((\w+)\))?", line)
        if m:
            if current:
                agents.append(current)
            current = {
                "name": m.group(1),
                "is_default": m.group(2) == "default",
                "identity": None,
                "workspace": None,
                "model": None,
                "routing_rules": 0,
            }
            continue
        if current is None:
            continue
        m = re.match(r"\s+Identity:\s*(.+?)\s*(?:\(config\)|\(IDENTITY\.md\))?$", line)
        if m:
            current["identity"] = m.group(1).strip()
            continue
        m = re.match(r"\s+Workspace:\s*(.+)$", line)
        if m:
            current["workspace"] = m.group(1).strip()
            continue
        m = re.match(r"\s+Model:\s*(.+)$", line)
        if m:
            current["model"] = m.group(1).strip()
            continue
        m = re.match(r"\s+Routing rules:\s*(\d+)", line)
        if m:
            current["routing_rules"] = int(m.group(1))
            continue

    if current:
        agents.append(current)
    return agents


def compute_activity_and_health(session, agent_name: str) -> tuple[str, str]:
    """Compute activity_status and health_status for an agent.

    active: any execution_record or subagent run or cron job in last N days
    error:  related execution_record result='failed' or cron job last_status='error'
    """
    window_days = settings.AGENT_ACTIVE_WINDOW_DAYS
    cutoff = (datetime.utcnow() - timedelta(days=window_days)).strftime("%Y-%m-%d")

    # Check execution records
    recent_exec = session.query(ExecutionRecord).filter(
        ExecutionRecord.business_line == agent_name,
        ExecutionRecord.date >= cutoff,
    ).count()

    # Check cron jobs (agent_id may or may not match; check name in cron title)
    error_cron = session.query(CronJob).filter(
        CronJob.name.ilike(f"%{agent_name}%"),
        CronJob.last_status == "error",
    ).count()

    # Check failed executions
    failed_exec = session.query(ExecutionRecord).filter(
        ExecutionRecord.business_line == agent_name,
        ExecutionRecord.result == "failed",
        ExecutionRecord.date >= cutoff,
    ).count()

    # Compute health
    if error_cron > 0 or failed_exec > 0:
        health = "error"
    elif recent_exec > 0:
        health = "ok"
    else:
        health = "warning"  # exists but no recent data

    # Compute activity
    activity = "active" if recent_exec > 0 else "inactive"

    return activity, health


def sync_agents() -> dict:
    """Multi-source agent sync: directory scan + CLI + activity computation.

    Does NOT clear and re-insert. Instead upserts: keeps discovered agents,
    updates registered status from CLI, recomputes activity/health.
    """
    session = get_sync_session()
    now_ts = now()

    try:
        # Step 1: Discover from directory
        discovered = scan_agent_directories()
        for name in discovered:
            existing = session.query(Agent).filter(Agent.name == name).first()
            if not existing:
                session.add(Agent(
                    id=name,
                    name=name,
                    discovery_status="discovered",
                    activity_status="inactive",
                    health_status="warning",
                    agent_type="openclaw",
                    status="offline",
                    created_at=now_ts,
                    updated_at=now_ts,
                ))

        # Step 2: Match against CLI registered agents
        registered_names: set[str] = set()
        try:
            result = subprocess.run(
                ["openclaw", "agents", "list"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                cli_agents = parse_agents_list(result.stdout)
                for a in cli_agents:
                    name = a["name"]
                    registered_names.add(name)
                    existing = session.query(Agent).filter(Agent.name == name).first()
                    if existing:
                        existing.discovery_status = "registered"
                        existing.identity = a.get("identity", existing.identity)
                        existing.workspace = a.get("workspace", existing.workspace)
                        existing.model = a.get("model", existing.model)
                        existing.routing_rules = a.get("routing_rules", existing.routing_rules) or 0
                        existing.is_default = 1 if a.get("is_default") else 0
                        existing.status = "online"
                    else:
                        # CLI registered but not in directory
                        session.add(Agent(
                            id=name,
                            name=name,
                            identity=a.get("identity"),
                            workspace=a.get("workspace"),
                            model=a.get("model"),
                            routing_rules=a.get("routing_rules", 0) or 0,
                            is_default=1 if a.get("is_default") else 0,
                            discovery_status="registered",
                            activity_status="inactive",
                            health_status="warning",
                            agent_type="openclaw",
                            status="online",
                            created_at=now_ts,
                            updated_at=now_ts,
                        ))
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass  # CLI not available — agents stay at discovered status

        # Mark unregistered: discovered but not in CLI output
        for name in discovered:
            if name not in registered_names:
                agent = session.query(Agent).filter(Agent.name == name).first()
                if agent and agent.discovery_status == "discovered":
                    agent.discovery_status = "unregistered"

        # Step 3: Compute activity + health for all agents
        all_agents = session.query(Agent).all()
        for agent in all_agents:
            activity, health = compute_activity_and_health(session, agent.name)
            agent.activity_status = activity
            agent.health_status = health
            agent.updated_at = now_ts

        session.commit()
        return {"status": "ok", "records": len(all_agents)}
    except Exception as e:
        session.rollback()
        return {"status": "error", "error": str(e), "records": 0}
    finally:
        session.close()
