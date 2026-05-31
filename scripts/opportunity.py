#!/usr/bin/env python3
"""
v0.31 — Opportunity Module Lite.

Asset types, Run Ledger events, and CLI for managing opportunities
as first-class OS objects. Works with local-only instance data (research/).

Three-layer boundary:
  Layer 1: ~/AI-Knowledge-OS/       — personal KB, never git
  Layer 2: research/                 — instance data, never git
  Layer 3: scripts/opportunity.py   — reusable framework, git
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from typing import Optional

# ── Paths ─────────────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
_BACKEND_DIR = os.path.join(_PROJECT_ROOT, "backend")

if os.path.isdir(_BACKEND_DIR):
    sys.path.insert(0, _BACKEND_DIR)

# Default pool directory (local-only, never committed)
_DEFAULT_POOL_DIR = os.path.join(_PROJECT_ROOT, "research", "opportunity-pool")


# ═══════════════════════════════════════════════════════════════
# Asset Types (Sprint B)
# ═══════════════════════════════════════════════════════════════

OPPORTUNITY_SIGNAL = "opportunity_signal"
OPPORTUNITY_CARD = "opportunity_card"
OPPORTUNITY_DECISION = "opportunity_decision"

ASSET_TYPES = [
    OPPORTUNITY_SIGNAL,
    OPPORTUNITY_CARD,
    OPPORTUNITY_DECISION,
]

# ═══════════════════════════════════════════════════════════════
# Run Ledger Event Types (Sprint B)
# ═══════════════════════════════════════════════════════════════

EVENT_SIGNAL_CREATED = "opportunity_signal_created"
EVENT_CARD_CREATED = "opportunity_card_created"
EVENT_APPROVED = "opportunity_approved"
EVENT_PARKED = "opportunity_parked"
EVENT_REJECTED = "opportunity_rejected"
EVENT_WORKFLOW_CREATED = "opportunity_workflow_created"

LEDGER_EVENTS = [
    EVENT_SIGNAL_CREATED,
    EVENT_CARD_CREATED,
    EVENT_APPROVED,
    EVENT_PARKED,
    EVENT_REJECTED,
    EVENT_WORKFLOW_CREATED,
]


# ═══════════════════════════════════════════════════════════════
# Pool Index Parsing
# ═══════════════════════════════════════════════════════════════

_STATUS_MAP = {
    # More specific prefixes first (check before generic "📋")
    "📋 New": "new",
    "📋 Pending": "pending",
    "🟢 Approved": "approved",
    "🅿️ Parked": "parked",
    "❌ Rejected": "rejected",
    "🔬 Deep Research": "deep_research",
    # Single-emoji fallbacks
    "📋": "pending",
    "🟢": "approved",
    "🅿️": "parked",
    "❌": "rejected",
    "🔬": "deep_research",
}

_EMOJI_REVERSE = {
    "new": "📋",
    "pending": "📋",
    "approved": "🟢",
    "parked": "🅿️",
    "rejected": "❌",
    "deep_research": "🔬",
}


def _normalize_status(raw: str) -> str:
    """Normalize emoji-status strings to canonical status names."""
    raw = raw.strip()
    for prefix, status in _STATUS_MAP.items():
        if raw.startswith(prefix):
            return status
    return raw.lower().replace(" ", "_")


def _format_status(status: str) -> str:
    """Format canonical status back to display string."""
    emoji = _EMOJI_REVERSE.get(status, "📋")
    name = status.replace("_", " ").title()
    return f"{emoji} {name}"


def find_pool_index(pool_dir: str = None) -> str:
    """Find the OPPORTUNITY-POOL-INDEX.md in the pool directory."""
    pool_dir = pool_dir or _DEFAULT_POOL_DIR
    candidates = [
        os.path.join(pool_dir, "OPPORTUNITY-POOL-INDEX.md"),
        os.path.join(pool_dir, "POOL-INDEX.md"),
        os.path.join(pool_dir, "pool-index.md"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[0]


def parse_pool_index(path: str) -> list[dict]:
    """Parse the pool index markdown table into structured records.

    Returns a list of dicts with keys:
        id, title, type, priority, founder_fit, time_to_mvp, status, next_action, cycle, raw_line

    Returns empty list if file doesn't exist or table not found.
    """
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the table — look for |---|--- lines
    lines = content.split("\n")
    table_start = None
    table_end = None

    for i, line in enumerate(lines):
        if re.match(r"^\|[-:| ]+\|", line):  # markdown table separator
            table_start = i + 1  # header row is before separator
            for j in range(i + 1, len(lines)):
                if not lines[j].strip().startswith("|"):
                    table_end = j
                    break
            if table_end is None:
                table_end = len(lines)
            break

    if table_start is None or table_end is None:
        return []

    # Parse header to find column indices
    header_line = lines[table_start - 2] if table_start >= 2 else ""
    headers = [h.strip() for h in header_line.strip("|").split("|")]

    # Find column indices
    col_map = {
        "id": next((i for i, h in enumerate(headers) if "id" in h.lower()), 0),
        "title": next((i for i, h in enumerate(headers) if "title" in h.lower()), 1),
        "type": next((i for i, h in enumerate(headers) if "type" in h.lower()), 2),
        "priority": next((i for i, h in enumerate(headers) if "prior" in h.lower()), 3),
        "founder_fit": next((i for i, h in enumerate(headers) if "founder" in h.lower() or "fit" in h.lower()), 4),
        "time_to_mvp": next((i for i, h in enumerate(headers) if "time" in h.lower() or "mvp" in h.lower()), 5),
        "status": next((i for i, h in enumerate(headers) if "status" in h.lower()), 6),
        "next_action": next((i for i, h in enumerate(headers) if "next" in h.lower() or "action" in h.lower()), 7),
        "cycle": next((i for i, h in enumerate(headers) if "cycle" in h.lower()), 8),
    }

    records = []
    for line_num in range(table_start, table_end):
        line = lines[line_num]
        if not line.strip().startswith("|"):
            continue

        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 3:
            continue

        def _col(idx):
            return cols[idx].strip() if idx < len(cols) else ""

        raw_status = _col(col_map["status"])
        raw_status_clean = raw_status.replace("**", "").strip()
        status = _normalize_status(raw_status_clean)
        is_current = "**" in _col(col_map["id"]) or "**" in _col(col_map["title"])

        records.append({
            "id": _col(col_map["id"]).replace("**", "").strip(),
            "title": _col(col_map["title"]).replace("**", "").strip(),
            "type": _col(col_map["type"]).replace("**", "").strip(),
            "priority": _col(col_map["priority"]).replace("**", "").strip(),
            "founder_fit": _col(col_map["founder_fit"]).replace("**", "").strip(),
            "time_to_mvp": _col(col_map["time_to_mvp"]).replace("**", "").strip(),
            "status": status,
            "status_raw": raw_status.replace("**", "").strip(),
            "next_action": _col(col_map["next_action"]).replace("**", "").strip(),
            "cycle": _col(col_map["cycle"]).replace("**", "").strip(),
            "is_current": is_current,
            "raw_line": line,
        })

    return records


def update_pool_index_status(path: str, op_id: str, new_status: str) -> bool:
    """Update the status column for a specific opportunity in the pool index.

    Returns True if updated, False otherwise.
    """
    records = parse_pool_index(path)
    target = next((r for r in records if r["id"] == op_id), None)
    if not target:
        return False

    old_line = target["raw_line"]
    new_status_display = _format_status(new_status)
    col_index = None

    # Find status column position in the raw line
    # The status is the column at index 6 (0-based) in the table
    cols = old_line.split("|")
    for i, c in enumerate(cols):
        if target["status_raw"].strip() == c.strip():
            col_index = i
            break

    if col_index is None:
        # Fallback: use column 6 (status column)
        col_index = min(6, len(cols) - 1)

    # Replace the status column value
    old_col = cols[col_index]
    new_col = old_col.replace(target["status_raw"].strip(), new_status_display)
    cols[col_index] = new_col
    new_line = "|".join(cols)

    # Read the full file and replace the line
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace(old_line, new_line)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return True


# ═══════════════════════════════════════════════════════════════
# Run Ledger Integration
# ═══════════════════════════════════════════════════════════════

def _record_event(event_type: str, op_id: str, summary: str, metadata: Optional[dict] = None):
    """Record a Run Ledger event for an opportunity action.

    Gracefully handles DB unavailable (prints warning, continues).
    """
    try:
        from app.services.run_ledger_service import record_and_register

        result = record_and_register(
            event_type=event_type,
            asset_type=OPPORTUNITY_DECISION,
            source_type="opportunity_cli",
            source_id=op_id,
            path=op_id,
            summary=summary,
            metadata=metadata or {},
        )
        if result:
            print(f"  📋 Run Ledger: {event_type} — {summary[:60]}")
        return result
    except Exception as e:
        print(f"  ⚠️  Run Ledger unavailable: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# Commands Implementation
# ═══════════════════════════════════════════════════════════════

def cmd_list(pool_dir: str = None, status_filter: str = None, status: str = None):
    """List all opportunities from the pool index."""
    # Accept both 'status' (from argparse) and 'status_filter' (internal)
    status_filter = status_filter or status
    index_path = find_pool_index(pool_dir)
    if not os.path.exists(index_path):
        print(f"❌ Pool index not found: {index_path}")
        print("   Create research/opportunity-pool/OPPORTUNITY-POOL-INDEX.md")
        return

    records = parse_pool_index(index_path)

    if not records:
        print(f"⚠️  No opportunities found in {index_path}")
        return

    if status_filter:
        records = [r for r in records if r["status"] == status_filter]

    if not records:
        print(f"⚠️  No opportunities with status '{status_filter}'")
        return

    print(f"\n{'ID':<12} {'Title':<45} {'Priority':<10} {'Status':<20} {'Next Action'}")
    print("-" * 110)
    for r in records:
        title = r["title"][:44]
        print(f"{r['id']:<12} {title:<45} {r['priority']:<10} {_format_status(r['status']):<20} {r['next_action']:<30}")

    print(f"\nTotal: {len(records)} opportunities")


def cmd_show(op_id: str, pool_dir: str = None):
    """Show details of a specific opportunity from its card file."""
    pool_dir = pool_dir or _DEFAULT_POOL_DIR

    # Look for card file
    card_files = [
        os.path.join(pool_dir, "OPPORTUNITY-CARDS-001.md"),
        os.path.join(pool_dir, "opportunity-cards.md"),
    ]

    for cf in card_files:
        if not os.path.exists(cf):
            continue

        with open(cf, "r", encoding="utf-8") as f:
            content = f.read()

        # Find the section for this OP
        # Sections start with "## OP-XXX:"
        pattern = re.compile(rf"(## {re.escape(op_id)}:.*?)(?=\n## |\Z)", re.DOTALL)
        match = pattern.search(content)
        if match:
            text = match.group(1).strip()
            print(f"\n{'=' * 60}")
            print(text)
            print(f"{'=' * 60}")
            return

    print(f"❌ Card not found for {op_id}")
    print(f"   Looked in: {', '.join(card_files)}")


def cmd_approve(op_id: str, pool_dir: str = None, note: str = ""):
    """Approve an opportunity — update index, record event, return decision data."""
    index_path = find_pool_index(pool_dir)
    records = parse_pool_index(index_path)
    target = next((r for r in records if r["id"] == op_id), None)

    if not target:
        print(f"❌ Opportunity not found: {op_id}")
        return None

    if target["status"] in ("approved",):
        print(f"⚠️  {op_id} is already approved")
        return None

    success = update_pool_index_status(index_path, op_id, "approved")
    if not success:
        print(f"❌ Failed to update pool index for {op_id}")
        return None

    summary = f"Approved: {target['title']}"
    if note:
        summary += f" — {note}"

    _record_event(EVENT_APPROVED, op_id, summary, {
        "title": target["title"],
        "priority": target["priority"],
        "founder_note": note,
        "previous_status": target["status"],
    })

    print(f"✅ {op_id} — {target['title']} — APPROVED")
    return {
        "op_id": op_id,
        "title": target["title"],
        "decision": "approved",
        "founder_note": note,
    }


def cmd_park(op_id: str, pool_dir: str = None, note: str = ""):
    """Park an opportunity."""
    index_path = find_pool_index(pool_dir)
    records = parse_pool_index(index_path)
    target = next((r for r in records if r["id"] == op_id), None)

    if not target:
        print(f"❌ Opportunity not found: {op_id}")
        return

    if target["status"] in ("parked",):
        print(f"⚠️  {op_id} is already parked")
        return

    success = update_pool_index_status(index_path, op_id, "parked")
    if not success:
        print(f"❌ Failed to update pool index for {op_id}")
        return

    summary = f"Parked: {target['title']}"
    if note:
        summary += f" — {note}"

    _record_event(EVENT_PARKED, op_id, summary, {
        "title": target["title"],
        "founder_note": note,
        "previous_status": target["status"],
    })

    print(f"🅿️  {op_id} — {target['title']} — PARKED")


def cmd_reject(op_id: str, pool_dir: str = None, note: str = ""):
    """Reject an opportunity."""
    index_path = find_pool_index(pool_dir)
    records = parse_pool_index(index_path)
    target = next((r for r in records if r["id"] == op_id), None)

    if not target:
        print(f"❌ Opportunity not found: {op_id}")
        return

    if target["status"] in ("rejected",):
        print(f"⚠️  {op_id} is already rejected")
        return

    success = update_pool_index_status(index_path, op_id, "rejected")
    if not success:
        print(f"❌ Failed to update pool index for {op_id}")
        return

    summary = f"Rejected: {target['title']}"
    if note:
        summary += f" — {note}"

    _record_event(EVENT_REJECTED, op_id, summary, {
        "title": target["title"],
        "founder_note": note,
        "previous_status": target["status"],
    })

    print(f"❌ {op_id} — {target['title']} — REJECTED")


def cmd_events(op_id: str = None):
    """Query Run Ledger for opportunity-related events."""
    try:
        from app.database import get_sync_session
        from app.models.run_ledger_event import RunLedgerEvent

        session = get_sync_session()
        query = session.query(RunLedgerEvent).filter(
            RunLedgerEvent.event_type.in_(LEDGER_EVENTS)
        )
        if op_id:
            query = query.filter(RunLedgerEvent.source_id == op_id)

        events = query.order_by(RunLedgerEvent.timestamp.desc()).limit(20).all()

        if not events:
            print("No opportunity events found in Run Ledger")
            return

        print(f"\n{'Event Type':<30} {'Source':<15} {'Timestamp':<25} {'Summary'}")
        print("-" * 110)
        for e in events:
            print(f"{e.event_type:<30} {e.source_id or '':<15} {str(e.timestamp)[:19]:<25} {(e.summary or '')[:60]}")
        print(f"\nTotal: {len(events)} events")

    except Exception as e:
        print(f"⚠️  Run Ledger unavailable: {e}")


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def build_parser(subparsers=None):
    """Build the argument parser for the opportunity module.

    Can work standalone (python3 scripts/opportunity.py <cmd>)
    or as a subparser of ceo_cmd.py.
    """
    if subparsers:
        parser = subparsers.add_parser("opportunity", help="Manage opportunities")
        sub = parser.add_subparsers(dest="opp_cmd", required=True)
    else:
        parser = argparse.ArgumentParser(description="Opportunity Module CLI")
        sub = parser.add_subparsers(dest="command", required=True)

    # --- list ---
    list_p = sub.add_parser("list", help="List all opportunities")
    list_p.add_argument("--status", "-s", help="Filter by status (new, pending, approved, parked, rejected)")
    list_p.add_argument("--pool-dir", default=None, help="Override pool directory")

    # --- show ---
    show_p = sub.add_parser("show", help="Show opportunity card details")
    show_p.add_argument("op_id", help="Opportunity ID (e.g., OP-001)")
    show_p.add_argument("--pool-dir", default=None, help="Override pool directory")

    # --- approve ---
    approve_p = sub.add_parser("approve", help="Approve an opportunity")
    approve_p.add_argument("op_id", help="Opportunity ID (e.g., OP-001)")
    approve_p.add_argument("--note", "-n", default="", help="Founder note")
    approve_p.add_argument("--pool-dir", default=None, help="Override pool directory")

    # --- park ---
    park_p = sub.add_parser("park", help="Park an opportunity")
    park_p.add_argument("op_id", help="Opportunity ID (e.g., OP-001)")
    park_p.add_argument("--note", "-n", default="", help="Founder note")
    park_p.add_argument("--pool-dir", default=None, help="Override pool directory")

    # --- reject ---
    reject_p = sub.add_parser("reject", help="Reject an opportunity")
    reject_p.add_argument("op_id", help="Opportunity ID (e.g., OP-001)")
    reject_p.add_argument("--note", "-n", default="", help="Founder note")
    reject_p.add_argument("--pool-dir", default=None, help="Override pool directory")

    # --- events ---
    events_p = sub.add_parser("events", help="Show opportunity events from Run Ledger")
    events_p.add_argument("op_id", nargs="?", help="Filter by opportunity ID")

    return parser if subparsers else parser


def main():
    """Main entry point for standalone usage."""
    parser = build_parser()
    args = parser.parse_args()
    cmd = args.opp_cmd if hasattr(args, "opp_cmd") else args.command

    if cmd == "list":
        cmd_list(args.pool_dir, args.status)
    elif cmd == "show":
        cmd_show(args.op_id, args.pool_dir)
    elif cmd == "approve":
        result = cmd_approve(args.op_id, args.pool_dir, args.note)
        if result:
            _maybe_create_workflow(result)
    elif cmd == "park":
        cmd_park(args.op_id, args.pool_dir, args.note)
    elif cmd == "reject":
        cmd_reject(args.op_id, args.pool_dir, args.note)
    elif cmd == "events":
        cmd_events(args.op_id)


# ═══════════════════════════════════════════════════════════════
# Workflow Bridge (Sprint D)
# ═══════════════════════════════════════════════════════════════

# Import at module level to avoid circular imports
_WORKFLOW_RUNNER = None


def _maybe_create_workflow(decision_data: dict):
    """If an opportunity was approved, prompt to create a follow-up workflow.

    Sprint D: bridges opportunity_approved → opportunity_followup_workflow.
    """
    if not decision_data:
        return

    print(f"\n  🔗 Bridge to Workflow Runner")
    print(f"     Approved: {decision_data['op_id']} — {decision_data['title']}")

    # Check if workflow_runner is available
    try:
        sys.path.insert(0, _SCRIPT_DIR)
        from workflow_runner import cmd_create

        # Create a workflow from the opportunity_followup_workflow template
        context_str = json.dumps({
            "opportunity_id": decision_data["op_id"],
            "founder_note": decision_data.get("founder_note", ""),
            "title": decision_data["title"],
        }, ensure_ascii=False)
        result = cmd_create(
            template_name="opportunity_followup_workflow",
            context=context_str,
        )

        if result:
            _record_event(EVENT_WORKFLOW_CREATED, decision_data["op_id"],
                          f"Workflow created: {result}",
                          {"workflow_id": result})
            print(f"  ✅ Workflow created: {result}")
            print(f"     Run: python3 scripts/workflow_runner.py status")
        else:
            print(f"  ⚠️  Workflow creation returned no result")

    except ImportError:
        print(f"  ⚠️  workflow_runner not available — install backend first")
    except Exception as e:
        print(f"  ⚠️  Workflow bridge error: {e}")


if __name__ == "__main__":
    main()
