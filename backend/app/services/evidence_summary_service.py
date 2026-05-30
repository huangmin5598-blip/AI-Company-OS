"""
v0.26 — Evidence Summary Service

Generates public-safe evidence summaries of AI Company OS activity.
Only outputs allowlisted fields — no paths, usernames, API keys, or raw prompts.

Usage (via ceo_cmd.py):
  python3 scripts/ceo_cmd.py evidence generate --format json
  python3 scripts/ceo_cmd.py evidence generate --format md
  python3 scripts/ceo_cmd.py evidence validate
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Paths ──
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_EVIDENCE_DIR = _PROJECT_ROOT / "docs" / "evidence"
_CAPABILITY_REGISTRY = _PROJECT_ROOT / "config" / "capability-registry.yaml"
_DECISION_LOG = _PROJECT_ROOT / "reports" / "ceo-brief-reviews" / "DECISION-LOG.md"

# ── Allowlist: ONLY these fields go into evidence output ──

ALLOWED_TOP_LEVEL = {
    "version",           # evidence version (v0.26)
    "generated_at",      # ISO timestamp
    "system",            # system metadata
    "milestones",        # version/release info
    "work_orders",       # WO counts (aggregated, no IDs/details)
    "run_ledger",        # event counts (aggregated)
    "assets",            # asset counts (aggregated)
    "capabilities",      # agent/capability summary
    "preflight",         # health check summary
    "governance",        # governance mechanism list
    "current_limitations",  # known limitations
}

ALLOWED_SYSTEM_FIELDS = {
    "name", "description", "architecture", "current_version",
    "local_first", "single_founder", "not_saas",
}

ALLOWED_WO_FIELDS = {"total", "by_status", "completed"}
ALLOWED_EVENT_FIELDS = {"total", "event_types"}
ALLOWED_ASSET_FIELDS = {"total", "asset_types"}
ALLOWED_CAPABILITY_FIELDS = {"total_agents", "by_runtime", "layer_summary"}
ALLOWED_PREFLIGHT_FIELDS = {"pass_count", "total", "all_pass", "check_names"}
ALLOWED_MILESTONE_FIELDS = {
    "versions_released", "latest_version", "first_version",
    "total_git_tags", "latest_tags",
}

# ── Sensitive patterns to sanitize ──

SENSITIVE_PATTERNS = [
    re.compile(r"/Users/[^/\s]+"),          # local absolute paths
    re.compile(r"/home/[^/\s]+"),            # Linux home dirs
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),      # OpenAI-style API keys
    re.compile(r"api[_-]?key['\"]?\s*[:=]\s*['\"][^'\"]+['\"]", re.IGNORECASE),  # api_key=xxx
    re.compile(r"token['\"]?\s*[:=]\s*['\"][^'\"]{8,}['\"]", re.IGNORECASE),     # token=xxx
    re.compile(r"password['\"]?\s*[:=]\s*['\"][^'\"]+['\"]", re.IGNORECASE),     # password=xxx
    re.compile(r"OPENAI_API_KEY|ANTHROPIC_API_KEY|OPENROUTER_API_KEY"),          # env var names
    re.compile(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b"),          # email addresses
    re.compile(r"(?:mongodb|postgresql|mysql)://[^@\s]+@"),                      # DB connection strings
]

_SANITIZE_CACHE: set = set()  # track what was sanitized for validation


def _sanitize(text: str) -> str:
    """Replace sensitive patterns with [REDACTED] and track what changed."""
    result = text
    for pattern in SENSITIVE_PATTERNS:
        matches = pattern.findall(result)
        for m in matches:
            _SANITIZE_CACHE.add(m[:60])  # truncate for cache
        result = pattern.sub("[REDACTED]", result)
    return result


def _get_latest_git_tags(limit: int = 5) -> list[str]:
    """Get the most recent git tags (public-safe, just version strings)."""
    try:
        result = subprocess.run(
            ["git", "tag", "--sort=-creatordate"],
            capture_output=True, text=True, timeout=5,
            cwd=str(_PROJECT_ROOT),
        )
        all_tags = [t.strip() for t in result.stdout.split("\n") if t.strip()]
        return all_tags, all_tags[:limit]
    except (subprocess.SubprocessError, FileNotFoundError):
        return [], ["unknown"]


def _count_decision_log_entries() -> int:
    """Count decision log entries without reading full content."""
    try:
        if _DECISION_LOG.exists():
            text_content = _DECISION_LOG.read_text(encoding="utf-8")
            # Count ## Decision headers
            return text_content.count("## Decision")
        return 0
    except (OSError, UnicodeDecodeError):
        return 0


def _load_capability_registry() -> dict[str, Any]:
    """Load capability registry (public-safe fields only)."""
    try:
        import yaml
        with open(_CAPABILITY_REGISTRY, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        agents = data.get("agents", [])
        by_runtime: dict[str, int] = {}
        layers: list[str] = []
        for agent in agents:
            runtime = agent.get("runtime", "unknown")
            by_runtime[runtime] = by_runtime.get(runtime, 0) + 1
            role = agent.get("role", "")
            if role and role not in layers:
                layers.append(role)

        return {
            "total_agents": len(agents),
            "by_runtime": by_runtime,
            "layer_summary": layers,
        }
    except Exception:
        return {"total_agents": 0, "by_runtime": {}, "layer_summary": []}


def _run_db_query(query: str) -> list[tuple]:
    """Run a raw DB query and return results."""
    try:
        sys.path.insert(0, str(_PROJECT_ROOT / "backend"))
        from app.database import get_sync_session
        from sqlalchemy import text

        session = get_sync_session()
        try:
            result = session.execute(text(query))
            rows = list(result)
            session.close()
            return rows
        except Exception:
            session.close()
            return []
    except Exception:
        return []


def generate_summary() -> dict[str, Any]:
    """Generate a public-safe evidence summary from live system data."""
    global _SANITIZE_CACHE
    _SANITIZE_CACHE = set()

    # ── DB Queries ──
    wo_status_rows = _run_db_query(
        "SELECT status, COUNT(*) as cnt FROM work_orders GROUP BY status"
    )
    wo_total_rows = _run_db_query("SELECT COUNT(*) FROM work_orders")
    evt_type_rows = _run_db_query(
        "SELECT event_type, COUNT(*) as cnt FROM run_ledger_events GROUP BY event_type"
    )
    evt_total_rows = _run_db_query("SELECT COUNT(*) FROM run_ledger_events")
    asset_type_rows = _run_db_query(
        "SELECT asset_type, COUNT(*) as cnt FROM asset_registry GROUP BY asset_type"
    )
    asset_total_rows = _run_db_query("SELECT COUNT(*) FROM asset_registry")

    # ── Compile data ──
    wo_total = wo_total_rows[0][0] if wo_total_rows else 0
    wo_by_status = {row[0]: row[1] for row in wo_status_rows} if wo_status_rows else {}
    evt_total = evt_total_rows[0][0] if evt_total_rows else 0
    evt_types = {row[0]: row[1] for row in evt_type_rows} if evt_type_rows else {}
    asset_total = asset_total_rows[0][0] if asset_total_rows else 0
    asset_types = {row[0]: row[1] for row in asset_type_rows} if asset_type_rows else {}

    capabilities = _load_capability_registry()
    all_tags, latest_tags = _get_latest_git_tags()
    decisions = _count_decision_log_entries()

    # ── Preflight summary ──
    preflight = {"pass_count": "?}", "total": "?", "all_pass": False, "check_names": []}
    # Import preflight checks if possible
    try:
        sys.path.insert(0, str(_PROJECT_ROOT / "backend"))
        from app.services.preflight_checks import run_all  # type: ignore
        pf_result = run_all()
        checks = pf_result.get("checks", [])
        passed = sum(1 for c in checks if c.get("status") == "pass")
        preflight = {
            "pass_count": passed,
            "total": len(checks),
            "all_pass": passed == len(checks),
            "check_names": [c.get("name", f"check_{i}") for i, c in enumerate(checks)],
        }
    except Exception:
        pass

    # ── Milestones ──
    milestones = {
        "versions_released": len(all_tags),
        "latest_version": latest_tags[0] if latest_tags else "v0.25",
        "first_version": all_tags[-1] if all_tags else "v0.17",
        "total_git_tags": len(all_tags),
        "latest_tags": latest_tags[:5],
    }

    # ── Governance mechanisms ──
    governance = {
        "mechanisms": [
            "CEO Brief → Review → Decision → Draft → Work Order → Approve → Execute → Callback → Result Sync",
            "Budget Guard — per-agent/per-task budget enforcement",
            "Failure Policy — automated retry, escalation, fallback",
            "Skill Router — capability-based task routing across runtimes",
            "Capability Registry — declarative agent capability declaration",
            "Preflight Checks — 11 health diagnostics",
            "Founder Console — read-only Founder control plane",
            "Asset Registry — idempotent pipeline asset tracking",
            "Run Ledger — event-sourced execution audit trail",
            "CEO Command Interface — structured OS CLI for Hermes/automation",
        ]
    }

    # ── Current limitations ──
    limitations = [
        "Local-first system — not a hosted SaaS platform",
        "Single-founder oriented — optimized for solo operator workflows",
        "No multi-user permission system — all operations are founder-trusted",
        "Evidence is summarized — not live public telemetry",
        "Founder approval still required for high-risk execution",
        "Some workflows remain CLI-assisted",
        "Screenshots in evidence doc are static snapshots",
    ]

    # ── Build output ──
    summary: dict[str, Any] = {
        "version": "v0.26",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "system": {
            "name": "AI Company OS",
            "description": "A governance-first operating system for AI-native companies — starting from solo founders",
            "architecture": (
                "5-layer: Execution Spine (WO pipeline), "
                "Governance Kernel (budget/failure/skill), "
                "Memory & Asset Layer (Run Ledger + Asset Registry), "
                "Founder Control Plane (Console + CEO Command), "
                "Productization & Evidence"
            ),
            "current_version": latest_tags[0] if latest_tags else "v0.25",
            "local_first": True,
            "single_founder": True,
            "not_saas": True,
        },
        "milestones": milestones,
        "work_orders": {
            "total": wo_total,
            "by_status": wo_by_status,
            "completed": wo_by_status.get("completed", 0),
        },
        "run_ledger": {
            "total": evt_total,
            "event_types": evt_types,
        },
        "assets": {
            "total": asset_total,
            "asset_types": asset_types,
        },
        "capabilities": capabilities,
        "preflight": preflight,
        "governance": governance,
        "current_limitations": limitations,
    }

    # ── Sanitize ──
    text = json.dumps(summary, indent=2, ensure_ascii=False)
    sanitized_text = _sanitize(text)
    if sanitized_text != text:
        summary = json.loads(sanitized_text)

    return summary


def generate_markdown(summary: dict[str, Any] | None = None) -> str:
    """Generate a public-safe evidence dashboard in Markdown."""
    if summary is None:
        summary = generate_summary()

    s = summary.get("system", {})
    w = summary.get("work_orders", {})
    r = summary.get("run_ledger", {})
    a = summary.get("assets", {})
    c = summary.get("capabilities", {})
    p = summary.get("preflight", {})
    m = summary.get("milestones", {})
    g = summary.get("governance", {})
    lim = summary.get("current_limitations", [])
    gen = summary.get("generated_at", "")

    lines = [
        "# AI Company OS — Evidence Dashboard Lite",
        "",
        f"> Generated: {gen}  |  Evidence Version: {summary.get('version', 'v0.26')}",
        "",
        "---",
        "",
        "## 1. What AI Company OS Is",
        "",
        f"{s.get('description', '')}",
        "",
        f"- **Current Version:** `{s.get('current_version', '?')}`",
        f"- **Local-First:** {s.get('local_first', True)}",
        f"- **Single-Founder Oriented:** {s.get('single_founder', True)}",
        f"- **Not a Hosted SaaS:** {s.get('not_saas', True)}",
        "",
        "---",
        "",
        "## 2. Architecture",
        "",
        f"{s.get('architecture', '')}",
        "",
        "```",
        "Execution Spine:  CEO Brief → Review → Decision → Draft",
        "                  → Work Order → Approve → Execute → Callback",
        "                  → Result Sync → Run Ledger / Asset Registry",
        "",
        "Founder Access:    Hermes Agent (Chief of Staff)",
        "                  ceo_cmd.py (Structured CLI)",
        "                  Control Center / Dashboard (Web UI)",
        "```",
        "",
        "---",
        "",
        "## 3. Version Milestones",
        "",
        f"| Metric | Value |",
        "|--------|-------|",
        f"| Versions Released | {m.get('versions_released', 0)} |",
        f"| Latest Version | `{m.get('latest_version', '?')}` |",
        f"| First Version | `{m.get('first_version', '?')}` |",
        f"| Total Git Tags | {m.get('total_git_tags', 0)} |",
        "",
        "Latest tags:",
        f"{', '.join(m.get('latest_tags', []))}",
        "",
        "---",
        "",
        "## 4. Decision-to-Execution Flow",
        "",
        "The core pipeline:",
        "",
        "1. **CEO Brief** — System-generated status summary for Founder",
        "2. **Review** — Founder reviews, decides next action",
        "3. **Decision** — Recorded in Decision Log",
        "4. **Draft** — Work Order Draft generated from decision",
        "5. **Work Order** — Dispatched to appropriate runtime",
        "6. **Approve** — Founder or automated approval",
        "7. **Execute** — Runtime executes via OpenClaw/Codex/Hermes",
        "8. **Callback** — Result returned via callback API",
        "9. **Result Sync** — Output backfilled to decision context",
        "",
        "All steps recorded in Run Ledger and Asset Registry.",
        "",
        "---",
        "",
        "## 5. Governance Mechanisms",
        "",
        "The system enforces the following governance:",
        "",
    ]

    for i, mech in enumerate(g.get("mechanisms", []), 1):
        lines.append(f"{i}. **{mech.split(' — ')[0]}**")
        desc = mech.split(" — ", 1)
        if len(desc) > 1:
            lines.append(f"   - {desc[1]}")
        lines.append("")

    lines += [
        "---",
        "",
        "## 6. Run Ledger Evidence",
        "",
        f"| Metric | Value |",
        "|--------|-------|",
        f"| Total Events | {r.get('total', 0)} |",
        f"| Event Types | {len(r.get('event_types', {}))} |",
        "",
        "Event type distribution:",
        "",
    ]

    for etype, count in sorted(r.get("event_types", {}).items()):
        bars = "█" * min(count, 30)
        lines.append(f"- `{etype}`: {count} {bars}")

    lines += [
        "",
        "![Skills Coverage Matrix](../screenshots/screenshot-skills.png)",
        "*Skills Coverage Matrix — agent skill mapping with coverage indicators*",
        "",
        "---",
        "",
        "## 7. Asset Registry Evidence",
        "",
        f"| Metric | Value |",
        "|--------|-------|",
        f"| Total Assets | {a.get('total', 0)} |",
        f"| Asset Types | {len(a.get('asset_types', {}))} |",
        "",
        "Asset type distribution:",
        "",
    ]

    for atype, count in sorted(a.get("asset_types", {}).items()):
        bars = "█" * min(count, 30)
        lines.append(f"- `{atype}`: {count} {bars}")

    lines += [
        "",
        "---",
        "",
        "## 8. Founder Control Center Evidence",
        "",
        "The Control Center provides a read-only Founder console with:",
        "",
        "- **5-Tab Navigation:** Dashboard, Workbench, Company, Products, Governance",
        "- **Founder Console Cards:** System health, WO status, recent events, assets",
        "- **Preflight Health Checks:** "
        + f"{p.get('pass_count', '?')}/{p.get('total', '?')} passing",
        "",
        "![Founder Console Dashboard](../screenshots/screenshot-dashboard.png)",
        "*Founder Console Dashboard — system overview, health checks, WO stats*",
        "",
        "![Preflight Health Checks](../screenshots/screenshot-preflight.png)",
        "*Preflight Health Checks — 11/11 all passing*",
        f"{'✅ All checks pass' if p.get('all_pass') else '⚠️ Some checks need attention'}",
        "",
    ]

    if p.get("check_names"):
        lines.append("Checks performed:")
        for name in p["check_names"]:
            dot = "✅" if p.get("all_pass") else "⬜"
            lines.append(f"- {dot} `{name}`")

    lines += [
        "",
        "---",
        "",
        "## 9. Runtime / Agent Evidence",
        "",
        f"| Metric | Value |",
        "|--------|-------|",
        f"| Total Agents | {c.get('total_agents', 0)} |",
    ]

    for runtime, count in c.get("by_runtime", {}).items():
        lines.append(f"| Runtime `{runtime}` Agents | {count} |")

    lines += [
        "",
        "Agent roles (layer summary):",
    ]
    for role in c.get("layer_summary", []):
        lines.append(f"- {role}")

    lines += [
        "",
        "![Workbench Tab](../screenshots/screenshot-workbench.png)",
        "*Workbench Tab — task pool, execution bridge, chat*",
        "",
        "![Agent List](../screenshots/screenshot-agents.png)",
        "*Agent List — runtime-grouped agent cards with status indicators*",
        "",
        "---",
        "",
        "## 10. Current Limitations",
        "",
    ]

    for lim_item in lim:
        lines.append(f"- {lim_item}")

    lines += [
        "",
        "---",
        "",
        "## 11. Next Roadmap",
        "",
        "- **v0.26** — Evidence Dashboard Lite + GitHub Refresh (current)",
        "- **v0.27** — Asset & Lineage Enhancement + Test Fixes",
        "- **v0.28** — Workflow Composition (WO `depends_on`, chains)",
        "- **v0.29+** — Further productization",
        "",
        "Full roadmap: [ROADWAY.md](/ROADMAP.md)",
        "",
        "---",
        "",
        f"*Evidence generated at {gen}*",
        "",
    ]

    return "\n".join(lines)


def save_evidence(summary: dict[str, Any] | None = None) -> tuple[str, str]:
    """Save evidence JSON and Markdown to docs/evidence/. Returns (json_path, md_path)."""
    if summary is None:
        summary = generate_summary()

    os.makedirs(str(_EVIDENCE_DIR), exist_ok=True)

    json_path = _EVIDENCE_DIR / "evidence-summary-v0.26.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    md_content = generate_markdown(summary)
    md_path = _EVIDENCE_DIR / "EVIDENCE-DASHBOARD-LITE-v0.26.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    return str(json_path), str(md_path)


def validate() -> dict[str, Any]:
    """Run validation checks on the evidence output. Returns a report."""
    global _SANITIZE_CACHE
    _SANITIZE_CACHE = set()

    # Generate and check
    summary = generate_summary()

    results: dict[str, Any] = {
        "valid": True,
        "checks": [],
        "sanitized_items": [],
        "errors": [],
    }

    # Check 1: JSON schema valid (can be re-serialized)
    try:
        json.dumps(summary, indent=2, ensure_ascii=False)
        results["checks"].append({"name": "json_serializable", "status": "pass"})
    except Exception as e:
        results["checks"].append({"name": "json_serializable", "status": "fail", "detail": str(e)})
        results["valid"] = False

    # Check 2: Allowlist compliance (no extra top-level keys)
    extra = set(summary.keys()) - ALLOWED_TOP_LEVEL
    if extra:
        results["checks"].append({
            "name": "allowlist_top_level",
            "status": "fail",
            "detail": f"Extra keys: {extra}",
        })
        results["valid"] = False
    else:
        results["checks"].append({"name": "allowlist_top_level", "status": "pass"})

    # Check 3: System fields allowlist
    sys_fields = set(summary.get("system", {}).keys())
    extra_sys = sys_fields - ALLOWED_SYSTEM_FIELDS
    if extra_sys:
        results["checks"].append({
            "name": "allowlist_system_fields",
            "status": "fail",
            "detail": f"Extra system fields: {extra_sys}",
        })
        results["valid"] = False
    else:
        results["checks"].append({"name": "allowlist_system_fields", "status": "pass"})

    # Check 4: No sensitive info in output
    serialized = json.dumps(summary, ensure_ascii=False)
    for pattern in SENSITIVE_PATTERNS:
        found = pattern.findall(serialized)
        if found:
            for item in found:
                results["sanitized_items"].append(item[:80])
    if results["sanitized_items"]:
        results["checks"].append({
            "name": "no_sensitive_data",
            "status": "fail",
            "detail": f"{len(results['sanitized_items'])} sensitive pattern(s) found",
        })
        results["valid"] = False
    else:
        results["checks"].append({"name": "no_sensitive_data", "status": "pass"})

    # Check 5: Markdown can be generated
    try:
        generate_markdown(summary)
        results["checks"].append({"name": "markdown_generatable", "status": "pass"})
    except Exception as e:
        results["checks"].append({
            "name": "markdown_generatable", "status": "fail", "detail": str(e),
        })
        results["valid"] = False

    # Check 6: No absolute paths
    abs_paths = re.findall(r"/[A-Za-z]/[^\s\"'{}()\[\],:;]*", serialized)
    local_paths = [p for p in abs_paths if not p.startswith("/api/") and len(p) > 15]
    if local_paths:
        results["checks"].append({
            "name": "no_absolute_paths",
            "status": "fail",
            "detail": f"Found {len(local_paths)} absolute path(s)",
        })
        results["valid"] = False
    else:
        results["checks"].append({"name": "no_absolute_paths", "status": "pass"})

    # Check 7: API key / token patterns
    key_patterns = re.findall(r"(?:sk-|api[_-]key|token|password)", serialized, re.IGNORECASE)
    if key_patterns:
        results["checks"].append({
            "name": "no_credentials",
            "status": "fail",
            "detail": f"Found {len(key_patterns)} credential pattern(s)",
        })
        results["valid"] = False
    else:
        results["checks"].append({"name": "no_credentials", "status": "pass"})

    # Check 8: Test baseline unchanged
    results["checks"].append({
        "name": "test_baseline",
        "status": "info",
        "detail": "Run `python3 -m pytest` to verify no regressions",
    })

    # Summary
    passed = sum(1 for c in results["checks"] if c["status"] == "pass")
    failed = sum(1 for c in results["checks"] if c["status"] == "fail")
    results["summary"] = {
        "total": len(results["checks"]),
        "pass": passed,
        "fail": failed,
        "info": sum(1 for c in results["checks"] if c["status"] == "info"),
    }

    return results
