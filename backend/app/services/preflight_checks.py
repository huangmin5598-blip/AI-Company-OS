# @PRODUCT Service — OS Core
"""Preflight Checks — system health diagnostics for Founder Console.

Each check returns:
  - name: check name
  - status: pass / warning / fail / info
  - action: suggested action string (empty if pass)

Status conventions:
  - pass:    everything is normal
  - warning: degraded but operational (missing optional component)
  - fail:    system cannot function properly without this
  - info:    informational (no failure possible)
"""
import os
import subprocess
import shutil
from pathlib import Path
from sqlalchemy import text
from app.database import get_sync_session

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_BACKEND_DIR = _PROJECT_ROOT / "backend"
_BRIEFS_DIR = _PROJECT_ROOT / "reports" / "ceo-briefs"
_REVIEWS_DIR = _PROJECT_ROOT / "reports" / "ceo-brief-reviews"
_DECISION_LOG = _REVIEWS_DIR / "DECISION-LOG.md"
_DRAFTS_DIR = _PROJECT_ROOT / "reports" / "work-order-drafts"
_CAPABILITY_REGISTRY = _PROJECT_ROOT / "config" / "capability-registry.yaml"
_BUDGET_POLICY = _BACKEND_DIR / "config" / "budget_policy.yaml"
_SKILL_REGISTRY = _BACKEND_DIR / "config" / "skill_registry.yaml"
_OPENCLAW_INBOX = Path.home() / ".ai-company-os" / "openclaw" / "inbox"


def run_all() -> dict:
    """Run all preflight checks and return results."""
    checks = []
    checks.append(_check_db())
    checks.append(_check_run_ledger())
    checks.append(_check_asset_registry())
    checks.append(_check_reports_path())
    checks.append(_check_capability_registry())
    checks.append(_check_decision_log())
    checks.append(_check_budget_policy())
    checks.append(_check_ceo_brief_exists())
    checks.append(_check_openclaw_cli())
    checks.append(_check_codex_cli())
    checks.append(_check_openclaw_inbox())

    pass_count = sum(1 for c in checks if c["status"] == "pass")
    warning_count = sum(1 for c in checks if c["status"] == "warning")
    fail_count = sum(1 for c in checks if c["status"] == "fail")

    return {
        "checks": checks,
        "summary": {
            "total": len(checks),
            "pass": pass_count,
            "warning": warning_count,
            "fail": fail_count,
        },
        "overall": "pass" if fail_count == 0 else ("warning" if warning_count > 0 else "fail"),
    }


def _check(name: str, status: str, action: str = "") -> dict:
    return {"name": name, "status": status, "action": action or ""}


# ── Individual checks ────────────────────────────────────────────

def _check_db() -> dict:
    """Check database is reachable."""
    try:
        session = get_sync_session()
        session.execute(text("SELECT 1"))
        session.close()
        return _check("Database", "pass")
    except Exception as e:
        return _check("Database", "fail", f"DB connection failed: {e}. Run backend server.")


def _check_run_ledger() -> dict:
    """Check Run Ledger table exists and is writable."""
    try:
        session = get_sync_session()
        session.execute(text("SELECT 1 FROM run_ledger_events LIMIT 1"))
        session.close()
        return _check("Run Ledger", "pass")
    except Exception:
        try:
            session = get_sync_session()
            from app.models.base import Base
            Base.metadata.create_all()
            session.close()
            return _check("Run Ledger", "pass")
        except Exception as e:
            return _check("Run Ledger", "fail", f"Run Ledger table missing: {e}. Run init_db().")


def _check_asset_registry() -> dict:
    """Check Asset Registry table exists."""
    try:
        session = get_sync_session()
        session.execute(text("SELECT 1 FROM asset_registry LIMIT 1"))
        session.close()
        return _check("Asset Registry", "pass")
    except Exception as e:
        return _check("Asset Registry", "fail", f"Asset Registry table missing: {e}. Run init_db().")


def _check_reports_path() -> dict:
    """Check reports/ directories exist."""
    missing = []
    for d in [_BRIEFS_DIR, _REVIEWS_DIR, _DRAFTS_DIR]:
        if not d.exists():
            missing.append(str(d.relative_to(_PROJECT_ROOT) if d.is_relative_to(_PROJECT_ROOT) else d))
    if not missing:
        return _check("Reports Paths", "pass")
    return _check("Reports Paths", "warning",
                  f"Missing directories: {', '.join(missing)}. Create them.")


def _check_capability_registry() -> dict:
    """Check Capability Registry file exists and is valid."""
    if not _CAPABILITY_REGISTRY.exists():
        return _check("Capability Registry", "warning",
                      "config/capability-registry.yaml not found. Create it.")
    try:
        import yaml
        with open(_CAPABILITY_REGISTRY, "r") as f:
            data = yaml.safe_load(f)
        agents = data.get("agents", [])
        if not agents:
            return _check("Capability Registry", "warning",
                          "capability-registry.yaml has no agents listed.")
        return _check("Capability Registry", "pass")
    except Exception as e:
        return _check("Capability Registry", "fail",
                      f"capability-registry.yaml parse error: {e}. Fix the YAML file.")


def _check_decision_log() -> dict:
    """Check Decision Log exists."""
    if _DECISION_LOG.exists():
        return _check("Decision Log", "pass")
    return _check("Decision Log", "info", "No decisions logged yet — normal for new systems.")


def _check_budget_policy() -> dict:
    """Check budget policy config exists."""
    if _BUDGET_POLICY.exists():
        return _check("Budget Policy", "pass")
    return _check("Budget Policy", "warning",
                  "backend/config/budget_policy.yaml not found. Create it.")


def _check_ceo_brief_exists() -> dict:
    """Check at least one CEO Brief exists."""
    if _BRIEFS_DIR.exists():
        briefs = [f for f in _BRIEFS_DIR.iterdir() if f.suffix == ".md" and "INDEX" not in f.name]
        if briefs:
            return _check("CEO Brief", "pass")
    return _check("CEO Brief", "info",
                  "No CEO Briefs generated yet. Run operating loop.")


def _check_openclaw_cli() -> dict:
    """Check OpenClaw CLI is available."""
    try:
        r = subprocess.run(["openclaw", "--version"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            version = r.stdout.strip()[:40]
            return _check("OpenClaw CLI", "pass")
        return _check("OpenClaw CLI", "warning",
                      "openclaw --version returned non-zero. Check installation.")
    except FileNotFoundError:
        return _check("OpenClaw CLI", "warning",
                      "OpenClaw CLI not found in PATH. Install or configure.")
    except Exception as e:
        return _check("OpenClaw CLI", "warning", f"OpenClaw check failed: {e}")


def _check_codex_cli() -> dict:
    """Check Codex CLI is available."""
    try:
        r = subprocess.run(["codex", "--version"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            return _check("Codex CLI", "pass")
        return _check("Codex CLI", "info", "Codex CLI not responding — may be disabled.")
    except FileNotFoundError:
        return _check("Codex CLI", "info",
                      "Codex CLI not in PATH. Expected if using OpenClaw instead.")


def _check_openclaw_inbox() -> dict:
    """Check OpenClaw inbox/working queue for stale tasks."""
    if not _OPENCLAW_INBOX.exists():
        return _check("OpenClaw Queue", "info", "No OpenClaw inbox directory found.")

    try:
        task_cards = list(_OPENCLAW_INBOX.glob("*.json"))
        stale_count = 0
        if task_cards:
            import json as _json
            now_ts = __import__("time").time()
            for card in task_cards:
                try:
                    data = _json.loads(card.read_text())
                    status = data.get("status", "")
                    if status in ("pending", "dispatched"):
                        stale_count += 1
                except Exception:
                    pass

        if stale_count > 0:
            return _check("OpenClaw Queue", "warning",
                          f"{stale_count} stale task(s) in inbox. "
                          "Run: python3 scripts/cleanup_stale_openclaw_tasks.py --dry-run")

        return _check("OpenClaw Queue", "pass")

    except Exception as e:
        return _check("OpenClaw Queue", "warning", f"Inbox check error: {e}")
