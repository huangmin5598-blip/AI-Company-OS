#!/usr/bin/env python3
"""
v0.24 — CEO Command Interface

Hermes / Founder 的安全 OS 操作接口。
只能查询状态、查询资产、生成 Draft，不能 create/approve/execute WO。

Usage:
    python3 scripts/ceo_cmd.py status [--since 24h]
    python3 scripts/ceo_cmd.py assets [--recent] [--limit 10]
    python3 scripts/ceo_cmd.py lineage <asset_id>
    python3 scripts/ceo_cmd.py draft-from-decision <decision_id>
    python3 scripts/ceo_cmd.py draft-from-asset <asset_id> [--summary "intent"]

All commands log actions to Run Ledger / ceo_action_log.
"""
import argparse
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone

# ── Backend path setup ─────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
_BACKEND_DIR = os.path.join(_PROJECT_ROOT, "backend")
sys.path.insert(0, _BACKEND_DIR)

from app.database import get_sync_session
from app.models.run_ledger_event import RunLedgerEvent
from app.models.asset_record import AssetRecord
from app.models.work_order import WorkOrder
from app.models.goal_session import GoalSession
from sqlalchemy import text

# ── Paths ─────────────────────────────────────────────────────────
BRIEFS_DIR = os.path.join(str(_PROJECT_ROOT), "reports", "ceo-briefs")
REVIEWS_DIR = os.path.join(str(_PROJECT_ROOT), "reports", "ceo-brief-reviews")
DECISION_LOG_PATH = os.path.join(REVIEWS_DIR, "DECISION-LOG.md")
DRAFTS_DIR = os.path.join(str(_PROJECT_ROOT), "reports", "work-order-drafts")

# ── Evidence Summary Service ─────────────────────────────────────
_EVIDENCE_DIR = os.path.join(str(_PROJECT_ROOT), "docs", "evidence")
_EVIDENCE_JSON = os.path.join(_EVIDENCE_DIR, "evidence-summary-v0.26.json")
_EVIDENCE_MD = os.path.join(_EVIDENCE_DIR, "EVIDENCE-DASHBOARD-LITE-v0.26.md")


# ── Helpers ───────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _log_action(action: str, detail: str = "", wo_id: str = "",
                decision_id: str = "", draft_id: str = "", asset_id: str = ""):
    """Log CEO action to Run Ledger."""
    try:
        from app.services.run_ledger_service import record_event
        record_event(
            event_type=f"ceo_{action}",
            source_type="cli",
            source_id=detail or action,
            work_order_id=wo_id,
            decision_id=decision_id,
            draft_id=draft_id,
            asset_id=asset_id,
            actor="ceo-cmd-interface",
            summary=f"CEO CMD: {action} — {detail[:120]}",
        )
    except Exception:
        pass  # non-fatal


# ── Status ────────────────────────────────────────────────────────

def cmd_status(since_hours: int = 24):
    """Query system status from Run Ledger + Work Orders + Decision Log."""
    session = get_sync_session()
    try:
        print("━" * 50)
        print("  🤖 AI Company OS — Status Summary")
        print(f"  Generated: {_now()}")
        print("━" * 50)

        # ── Work Orders summary ──
        total_wo = session.query(WorkOrder).count()
        by_status = {}
        for row in session.query(WorkOrder.status, text("COUNT(*) as cnt")).group_by(WorkOrder.status).all():
            by_status[row[0]] = row[1]

        print(f"\n  📋 Work Orders ({total_wo})")
        for s in ["created", "routed", "in_progress", "completed", "failed", "cancelled", "needs_review"]:
            if s in by_status:
                icon = {"completed": "✅", "failed": "❌", "in_progress": "🔄", "cancelled": "⏭️",
                        "needs_review": "⚠️", "created": "📝", "routed": "📎"}.get(s, "•")
                print(f"    {icon} {s}: {by_status[s]}")

        # Recent WO completions
        recent_completed = session.query(WorkOrder).filter(
            WorkOrder.status == "completed"
        ).order_by(WorkOrder.completed_at.desc()).limit(3).all()
        if recent_completed:
            print(f"\n  Recent completions:")
            for wo in recent_completed:
                ts = ""
                if wo.completed_at:
                    completed_str = str(wo.completed_at)
                    ts = completed_str[:16]
                summary = (wo.result_summary or "")[:60]
                print(f"    ✅ {wo.work_order_id} ({ts}) — {summary}")

        # ── Run Ledger recent events ──
        recent_events = session.query(RunLedgerEvent).order_by(
            RunLedgerEvent.timestamp.desc()
        ).limit(5).all()
        if recent_events:
            print(f"\n  📋 Recent Events:")
            for e in recent_events:
                refs = []
                if e.work_order_id: refs.append(e.work_order_id)
                if e.decision_id: refs.append(e.decision_id)
                ref_str = f" [{', '.join(refs)}]" if refs else ""
                print(f"    [{e.event_type}]{ref_str} — {e.summary[:80] or '—'}")

        # ── Assets ──
        total_assets = session.query(AssetRecord).count()
        by_type = {}
        for row in session.query(AssetRecord.asset_type, text("COUNT(*) as cnt")).group_by(AssetRecord.asset_type).all():
            by_type[row[0]] = row[1]
        print(f"\n  📦 Assets ({total_assets})")
        asset_icons = {"ceo_brief": "📄", "ceo_brief_review": "📝", "decision_log_entry": "📋",
                       "work_order_draft": "📎", "work_order": "🔄", "execution_result": "✅"}
        for atype, count in sorted(by_type.items()):
            icon = asset_icons.get(atype, "📦")
            print(f"    {icon} {atype}: {count}")

        # ── Decisions / Drafts ──
        if os.path.exists(DECISION_LOG_PATH):
            with open(DECISION_LOG_PATH, "r") as f:
                log_text = f.read()
            # Count decisions without Execution Completed status
            lines = log_text.strip().split("\n")
            decision_rows = [l for l in lines if l.startswith("|") and "DEC-" in l]
            executed = sum(1 for l in decision_rows if "Execution Completed" in l)
            pending = len(decision_rows) - executed
            print(f"\n  📋 Decision Log: {len(decision_rows)} total ({executed} executed, {pending} pending)")

        # Drafts
        if os.path.exists(DRAFTS_DIR):
            drafts = [f for f in os.listdir(DRAFTS_DIR) if f.startswith("WO-DRAFT-") and f.endswith(".md")]
            pending_drafts = 0
            for d in drafts:
                with open(os.path.join(DRAFTS_DIR, d), "r") as f:
                    content = f.read()
                if "_draft_status: draft" in content or "_draft_status: created" in content:
                    pending_drafts += 1
            print(f"  📎 Drafts: {len(drafts)} total ({pending_drafts} pending)")

        # ── Recent CEO Briefs ──
        if os.path.exists(BRIEFS_DIR):
            briefs = [f for f in os.listdir(BRIEFS_DIR) if f.endswith(".md") and "INDEX" not in f]
            if briefs:
                latest = sorted(briefs)[-1]
                print(f"\n  💼 Latest Brief: {latest}")

        # ── Risks / blockers ──
        risks = []
        if "failed" in by_status:
            risks.append(f"{by_status['failed']} failed WO(s)")
        if "needs_review" in by_status:
            risks.append(f"{by_status['needs_review']} WO(s) need review")
        if pending > 0:
            risks.append(f"{pending} unexecuted decision(s)")
        if risks:
            print(f"\n  ⚠️  Risks / Blockers:")
            for r in risks:
                print(f"    • {r}")
        else:
            print(f"\n  ✅ No blockers detected")

        print()
        _log_action("status", f"system status summary ({total_wo} WO, {total_assets} assets)")

    finally:
        session.close()


# ── Assets ────────────────────────────────────────────────────────

def cmd_assets(limit: int = 10):
    """List recent assets."""
    session = get_sync_session()
    try:
        assets = session.query(AssetRecord).order_by(
            AssetRecord.created_at.desc()
        ).limit(limit).all()

        if not assets:
            print("  ℹ️  No assets found")
            return

        print(f"  📦 Recent Assets ({len(assets)})\n")
        for a in assets:
            refs = []
            if a.source_work_order: refs.append(f"wo={a.source_work_order}")
            if a.source_decision: refs.append(f"dec={a.source_decision}")
            ref_str = f" [{', '.join(refs)}]" if refs else ""
            print(f"  [{a.asset_type}] {a.id}{ref_str}")
            print(f"    path:    {a.path or '—'}")
            print(f"    summary: {a.summary or '—'}")
            print(f"    created: {a.created_at}")
            print()

        _log_action("assets", f"listed {len(assets)} recent assets")

    finally:
        session.close()


# ── Lineage ───────────────────────────────────────────────────────

def cmd_lineage(asset_id: str):
    """Show asset lineage (wraps os_registry.py logic)."""
    session = get_sync_session()
    try:
        asset = session.query(AssetRecord).filter(AssetRecord.id == asset_id).first()
        if not asset:
            print(f"  ❌ Asset not found: {asset_id}")
            return

        print(f"\n  🔗 Asset Lineage — {asset.id}")
        print(f"  {'=' * 50}")

        print(f"\n  📄 Current Asset")
        print(f"    type:      {asset.asset_type}")
        print(f"    path:      {asset.path or '—'}")
        print(f"    summary:   {asset.summary or '—'}")
        print(f"    status:    {asset.status}")
        print(f"    created:   {asset.created_at}")

        sources = []
        if asset.source_brief:
            sources.append(("Brief", asset.source_brief))
        if asset.source_decision:
            sources.append(("Decision", asset.source_decision))
        if asset.source_draft:
            sources.append(("Draft", asset.source_draft))
        if asset.source_work_order:
            sources.append(("Work Order", asset.source_work_order))

        if sources:
            print(f"\n  ⬆️  Source Chain")
            for label, val in sources:
                print(f"    {label:<15} {val}")

        events = session.query(RunLedgerEvent).filter(
            RunLedgerEvent.asset_id == asset_id
        ).order_by(RunLedgerEvent.timestamp.asc()).all()
        if events:
            print(f"\n  📋 Related Events ({len(events)})")
            for e in events:
                print(f"    [{e.event_type}] {e.timestamp} — {e.summary or '—'}")

        children = session.query(AssetRecord).filter(
            (AssetRecord.source_brief == asset.path) |
            (AssetRecord.source_decision == asset.source_decision) |
            (AssetRecord.source_draft == asset.source_draft) |
            (AssetRecord.source_work_order == asset.source_work_order)
        ).filter(AssetRecord.id != asset_id).all()

        if children:
            print(f"\n  ⬇️  Derived Assets ({len(children)})")
            for c in children:
                print(f"    [{c.asset_type}] {c.id} — {c.summary or c.path or '—'}")

        print()
        _log_action("lineage", f"asset {asset_id}")

    finally:
        session.close()


# ── Draft from Decision ────────────────────────────────────────────

def _parse_decision_row(line: str) -> dict:
    """Parse a DECISION-LOG.md table row into a dict."""
    parts = [p.strip() for p in line.split("|")]
    if len(parts) < 7:
        return {}
    return {
        "date": parts[1],
        "decision_id": parts[2],
        "source_brief": parts[3],
        "summary": parts[4],
        "founder_decision": parts[5],
        "notes": parts[6] if len(parts) > 6 else "",
    }


def cmd_draft_from_decision(decision_id: str):
    """Generate a Work Order Draft from a decision entry."""
    if not os.path.exists(DECISION_LOG_PATH):
        print(f"  ❌ Decision log not found: {DECISION_LOG_PATH}")
        return

    # Find the decision in the log
    decision = None
    with open(DECISION_LOG_PATH, "r") as f:
        for line in f:
            if decision_id in line and line.startswith("|"):
                entry = _parse_decision_row(line)
                if entry.get("decision_id") == decision_id:
                    # Skip already executed decisions
                    if "Execution Completed" in line:
                        print(f"  ℹ️  Decision {decision_id} already executed")
                        return
                    decision = entry
                    break

    if not decision:
        print(f"  ❌ Decision not found: {decision_id}")
        print(f"  Use 'python3 scripts/ceo_cmd.py status' to see decisions")
        return

    # Generate draft
    now = _now()
    dt = datetime.now()
    drafts = [f for f in os.listdir(DRAFTS_DIR) if f.startswith("WO-DRAFT-")] if os.path.exists(DRAFTS_DIR) else []
    next_idx = len(drafts) + 1
    draft_id = f"WO-DRAFT-{dt.strftime('%Y%m%d')}-{next_idx:03d}"

    os.makedirs(DRAFTS_DIR, exist_ok=True)

    title = decision["summary"][:80]
    source_brief = decision.get("source_brief", "unknown")
    notes = decision.get("notes", "(none)")

    draft_content = f"""# Work Order Draft

**Draft ID:** {draft_id}
**Source Brief:** {source_brief}
**Source Decision:** {decision_id}
**Decision Type:** maintenance
**Risk Level:** medium
**Approval Required:** true
**Created:** {now}
**Generated By:** ceo-cmd-interface

---
## Auto-filled Title

{title}

---
## Founder To Fill

**Suggested Task Type:**
```
TODO: Founder to fill
```

**Suggested Skill:**
```
TODO: Founder to fill
```

**Suggested Agent:**
```
TODO: Founder to fill
```

**Proposed Prompt:**
```
Based on decision {decision_id}: {title}
```

**Expected Output:**
```
TODO: Founder to fill
```

---
## Founder Confirmation

- [ ] approve_create_work_order (确认创建 Work Order)
- [ ] edit_required (需要修改)
- [ ] dismiss (放弃此草稿)

---
## Notes

_{notes}_

---
_draft_status: draft_
"""

    draft_path = os.path.join(DRAFTS_DIR, f"{draft_id}.md")
    with open(draft_path, "w", encoding="utf-8") as f:
        f.write(draft_content)

    print(f"  ✅ Draft generated: reports/work-order-drafts/{draft_id}.md")
    print(f"     Decision:      {decision_id}")
    print(f"     Source Brief:  {source_brief}")
    print(f"     Summary:       {title}")
    print()
    print(f"  ℹ️  Next step: Founder fills required fields + confirms create-work-order")
    print(f"     → python3 scripts/review_brief.py create-work-order reports/work-order-drafts/{draft_id}.md")
    print()

    _log_action("draft_from_decision", f"generated {draft_id} from {decision_id}",
                decision_id=decision_id, draft_id=draft_id)


def cmd_draft_from_asset(asset_id: str, summary: str = ""):
    """Generate a follow-up Work Order Draft from an existing asset."""
    session = get_sync_session()
    try:
        asset = session.query(AssetRecord).filter(AssetRecord.id == asset_id).first()
        if not asset:
            print(f"  ❌ Asset not found: {asset_id}")
            return

        now = _now()
        dt = datetime.now()
        drafts = [f for f in os.listdir(DRAFTS_DIR) if f.startswith("WO-DRAFT-")] if os.path.exists(DRAFTS_DIR) else []
        next_idx = len(drafts) + 1
        draft_id = f"WO-DRAFT-{dt.strftime('%Y%m%d')}-{next_idx:03d}"

        os.makedirs(DRAFTS_DIR, exist_ok=True)

        title = summary or f"Follow-up from {asset.asset_type} {asset_id}"
        notes = f"Generated from asset {asset_id} ({asset.asset_type}): {asset.summary or asset.path or ''}"

        draft_content = f"""# Work Order Draft

**Draft ID:** {draft_id}
**Source Asset:** {asset_id} ({asset.asset_type})
**Source Brief:** {asset.source_brief or '—'}
**Source Decision:** {asset.source_decision or '—'}
**Source Work Order:** {asset.source_work_order or '—'}
**Decision Type:** maintenance
**Risk Level:** medium
**Approval Required:** true
**Created:** {now}
**Generated By:** ceo-cmd-interface

---
## Auto-filled Title

{title}

---
## Founder To Fill

**Suggested Task Type:**
```
TODO: Founder to fill
```

**Suggested Skill:**
```
TODO: Founder to fill
```

**Suggested Agent:**
```
TODO: Founder to fill
```

**Proposed Prompt:**
```
Follow-up task from {asset.asset_type} {asset_id}: {title}
```

**Expected Output:**
```
TODO: Founder to fill
```

---
## Founder Confirmation

- [ ] approve_create_work_order (确认创建 Work Order)
- [ ] edit_required (需要修改)
- [ ] dismiss (放弃此草稿)

---
## Notes

_{notes}_

---
_draft_status: draft_
"""

        draft_path = os.path.join(DRAFTS_DIR, f"{draft_id}.md")
        with open(draft_path, "w", encoding="utf-8") as f:
            f.write(draft_content)

        print(f"  ✅ Draft generated: reports/work-order-drafts/{draft_id}.md")
        print(f"     Source Asset:  {asset_id} ({asset.asset_type})")
        print(f"     Summary:       {title}")
        print()
        print(f"  ℹ️  Next step: Founder fills required fields + confirms create-work-order")
        print(f"     → python3 scripts/review_brief.py create-work-order reports/work-order-drafts/{draft_id}.md")
        print()

        _log_action("draft_from_asset", f"generated {draft_id} from {asset_id}",
                    asset_id=asset_id, draft_id=draft_id)

    finally:
        session.close()


# ── Evidence Commands ────────────────────────────────────────────

def cmd_evidence(args: argparse.Namespace) -> None:
    """Handle evidence subcommands: generate, validate."""
    # Import the service (lazy import to keep startup fast)
    try:
        sys.path.insert(0, _BACKEND_DIR)
        from app.services.evidence_summary_service import (
            generate_summary, generate_markdown, save_evidence, validate as ev_validate,
        )
    except ImportError as e:
        print(f"  ❌ Evidence service unavailable: {e}")
        print(f"     Expected at backend/app/services/evidence_summary_service.py")
        sys.exit(1)

    if args.evidence_cmd == "generate":
        fmt = args.format
        print(f"  📊 Generating evidence summary...")
        print()

        if fmt in ("json", "both"):
            json_path, _ = save_evidence()
            print(f"  ✅ JSON:     {json_path}")
            with open(json_path) as f:
                data = json.load(f)
            w = data.get("work_orders", {})
            r = data.get("run_ledger", {})
            a = data.get("assets", {})
            p = data.get("preflight", {})
            print(f"     WO: {w.get('total', 0)} total, {w.get('completed', 0)} completed")
            print(f"     Events: {r.get('total', 0)} events, {len(r.get('event_types', {}))} types")
            print(f"     Assets: {a.get('total', 0)} records, {len(a.get('asset_types', {}))} types")
            print(f"     Preflight: {p.get('pass_count', '?')}/{p.get('total', '?')} pass")
            print()

        if fmt in ("md", "both"):
            summary = generate_summary() if fmt == "md" else data
            md_content = generate_markdown(summary)
            os.makedirs(_EVIDENCE_DIR, exist_ok=True)
            with open(_EVIDENCE_MD, "w") as f:
                f.write(md_content)
            print(f"  ✅ Markdown: {_EVIDENCE_MD}")
            # Count non-empty sections
            section_count = md_content.count("\n## ")
            print(f"     {section_count} sections in evidence document")
            print()

        print(f"  ℹ️  Next: update README.md and ROADMAP.md to reference evidence docs")
        print(f"     → ceo evidence validate")

    elif args.evidence_cmd == "validate":
        print(f"  🔍 Validating evidence output...")
        print()
        result = ev_validate()
        for check in result.get("checks", []):
            icon = "✅" if check["status"] == "pass" else "❌" if check["status"] == "fail" else "ℹ️"
            detail = check.get("detail", "")
            print(f"  {icon} {check['name']}: {check['status']}")
            if detail:
                print(f"     {detail}")

        summary = result.get("summary", {})
        print()
        print(f"  {'✅ VALID' if result.get('valid') else '❌ INVALID'} — "
              f"{summary.get('pass', 0)}/{summary.get('total', 0)} checks pass, "
              f"{summary.get('fail', 0)} failed")

        if result.get("sanitized_items"):
            print(f"  ⚠️  {len(result['sanitized_items'])} sensitive pattern(s) sanitized:")
            for item in result["sanitized_items"][:5]:
                print(f"     → {item}")

        if not result.get("valid"):
            sys.exit(1)


# ── Main ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="v0.24 — CEO Command Interface: query system, generate drafts"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    status_p = subparsers.add_parser("status", help="System status summary")
    status_p.add_argument("--since", default="24h", help="Time window (default: 24h)")

    # assets
    assets_p = subparsers.add_parser("assets", help="List recent assets")
    assets_p.add_argument("--limit", type=int, default=10, help="Max assets (default: 10)")

    # lineage
    lineage_p = subparsers.add_parser("lineage", help="Show asset lineage")
    lineage_p.add_argument("asset_id", help="Asset ID (e.g. ast-XXXX)")

    # draft-from-decision
    dfd_p = subparsers.add_parser("draft-from-decision", help="Generate Draft from decision")
    dfd_p.add_argument("decision_id", help="Decision ID (e.g. DEC-20260530-001)")

    # draft-from-asset
    dfa_p = subparsers.add_parser("draft-from-asset", help="Generate follow-up Draft from asset")
    dfa_p.add_argument("asset_id", help="Asset ID (e.g. ast-XXXX)")
    dfa_p.add_argument("--summary", default="", help="Optional summary for the draft title")

    # evidence
    ev_p = subparsers.add_parser("evidence", help="Evidence summary operations")
    ev_sub = ev_p.add_subparsers(dest="evidence_cmd", required=True)

    ev_gen = ev_sub.add_parser("generate", help="Generate evidence summary")
    ev_gen.add_argument("--format", default="both", choices=["json", "md", "both"],
                        help="Output format (default: both)")

    ev_sub.add_parser("validate", help="Validate evidence output")

    args = parser.parse_args()

    if args.command == "status":
        cmd_status()
    elif args.command == "assets":
        cmd_assets(limit=args.limit)
    elif args.command == "lineage":
        cmd_lineage(args.asset_id)
    elif args.command == "draft-from-decision":
        cmd_draft_from_decision(args.decision_id)
    elif args.command == "draft-from-asset":
        cmd_draft_from_asset(args.asset_id, summary=args.summary)
    elif args.command == "evidence":
        cmd_evidence(args)


if __name__ == "__main__":
    main()
