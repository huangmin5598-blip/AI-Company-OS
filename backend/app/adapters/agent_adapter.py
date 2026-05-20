"""Adapter: sync agents from `openclaw agents list` CLI."""
import subprocess
import re
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from app.database import get_sync_session
from app.models.agent import Agent
from app.config import settings

def now():
    return datetime.utcnow().isoformat() + "Z"

def parse_agents_list(output: str) -> list[dict]:
    """Parse `openclaw agents list` CLI output into structured records."""
    agents = []
    current = None
    
    for line in output.split("\n"):
        line = line.rstrip()
        
        # Agent header: "- main (default)"
        m = re.match(r"^- (\w[\w-]*)\s*(?:\((\w+)\))?", line)
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
        
        # Identity: "  Identity: 😎 Tiger-编程专家 (config)"
        m = re.match(r"\s+Identity:\s*(.+?)\s*(?:\(config\)|\(IDENTITY\.md\))?$", line)
        if m:
            current["identity"] = m.group(1).strip()
            continue
        
        # Workspace: "  Workspace: ~/.openclaw/workspace-tiger-coder"
        m = re.match(r"\s+Workspace:\s*(.+)$", line)
        if m:
            current["workspace"] = m.group(1).strip()
            continue
        
        # Model: "  Model: minimax-cn/MiniMax-M2.5"
        m = re.match(r"\s+Model:\s*(.+)$", line)
        if m:
            current["model"] = m.group(1).strip()
            continue
        
        # Routing rules: "  Routing rules: 1"
        m = re.match(r"\s+Routing rules:\s*(\d+)", line)
        if m:
            current["routing_rules"] = int(m.group(1))
            continue
    
    if current:
        agents.append(current)
    
    return agents


def sync_agents() -> dict:
    """Sync agents from openclaw CLI to SQLite."""
    session = get_sync_session()
    try:
        # Run CLI
        result = subprocess.run(
            ["openclaw", "agents", "list"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return {"status": "error", "error": result.stderr.strip(), "records": 0}
        
        agents_data = parse_agents_list(result.stdout)
        
        # Clear existing agents
        session.query(Agent).delete()
        
        # Insert fresh data
        for a in agents_data:
            session.add(Agent(
                id=a["name"],
                name=a["name"],
                identity=a.get("identity"),
                workspace=a.get("workspace"),
                model=a.get("model"),
                routing_rules=a.get("routing_rules", 0) or 0,
                is_default=1 if a.get("is_default") else 0,
                agent_type="openclaw",
                status="online",
                last_active_at=now(),
                created_at=now(),
                updated_at=now(),
            ))
        
        session.commit()
        return {"status": "ok", "records": len(agents_data)}
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "CLI timeout (30s)", "records": 0}
    except FileNotFoundError:
        return {"status": "error", "error": "openclaw CLI not found", "records": 0}
    except Exception as e:
        session.rollback()
        return {"status": "error", "error": str(e), "records": 0}
    finally:
        session.close()
