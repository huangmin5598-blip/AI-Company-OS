#!/usr/bin/env python3
"""
v0.23 — OS Registry CLI: query Run Ledger, Asset Registry, and lineage.

Usage:
    python3 scripts/os_registry.py ledger recent [--limit 20] [--type EVENT_TYPE]
    python3 scripts/os_registry.py assets list [--type ASSET_TYPE] [--limit 20]
    python3 scripts/os_registry.py lineage <asset_id>

Examples:
    python3 scripts/os_registry.py ledger recent
    python3 scripts/os_registry.py ledger recent --type work_order_created
    python3 scripts/os_registry.py assets list --type execution_result
    python3 scripts/os_registry.py lineage ast-XXXX
"""
import argparse
import os
import sys

# ── Backend path setup ─────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
_BACKEND_DIR = os.path.join(_PROJECT_ROOT, "backend")
sys.path.insert(0, _BACKEND_DIR)

from app.database import get_sync_session
from app.models.run_ledger_event import RunLedgerEvent
from app.models.asset_record import AssetRecord


# ── Formatters ─────────────────────────────────────────────────────

def _fmt_row(label: str, value: str, width: int = 30) -> str:
    return f"  {label:<{width}} {value}"


def _print_event(evt) -> None:
    print(f"  [{evt.event_type}]")
    print(f"    id:        {evt.id}")
    print(f"    source_id: {evt.source_id or '—'}")
    cols = []
    if evt.work_order_id: cols.append(f"wo={evt.work_order_id}")
    if evt.decision_id: cols.append(f"dec={evt.decision_id}")
    if evt.draft_id: cols.append(f"draft={evt.draft_id}")
    if evt.asset_id: cols.append(f"asset={evt.asset_id}")
    if cols:
        print(f"    refs:      {', '.join(cols)}")
    print(f"    time:      {evt.timestamp}")
    print(f"    summary:   {evt.summary or '—'}")
    print()


def _print_asset(a) -> None:
    print(f"  [{a.asset_type}] {a.id}")
    print(f"    path:      {a.path or '—'}")
    cols = []
    if a.source_brief: cols.append(f"brief={a.source_brief}")
    if a.source_decision: cols.append(f"dec={a.source_decision}")
    if a.source_draft: cols.append(f"draft={a.source_draft}")
    if a.source_work_order: cols.append(f"wo={a.source_work_order}")
    if cols:
        print(f"    sources:   {', '.join(cols)}")
    print(f"    status:    {a.status}")
    print(f"    created:   {a.created_at}")
    if a.tags:
        print(f"    tags:      {a.tags}")
    if a.summary:
        print(f"    summary:   {a.summary}")
    print()


# ── Subcommands ───────────────────────────────────────────────────

def cmd_ledger_recent(limit: int = 20, event_type: str = "") -> None:
    session = get_sync_session()
    try:
        query = session.query(RunLedgerEvent)
        if event_type:
            query = query.filter(RunLedgerEvent.event_type == event_type)
        events = query.order_by(RunLedgerEvent.timestamp.desc()).limit(limit).all()

        if not events:
            print(f"  ℹ️  No ledger events found" +
                  (f" of type '{event_type}'" if event_type else ""))
            return

        print(f"  📋 Run Ledger — Recent Events ({len(events)})\n")
        for evt in events:
            _print_event(evt)
    finally:
        session.close()


def cmd_assets_list(asset_type: str = "", limit: int = 20) -> None:
    session = get_sync_session()
    try:
        query = session.query(AssetRecord)
        if asset_type:
            query = query.filter(AssetRecord.asset_type == asset_type)
        assets = query.order_by(AssetRecord.created_at.desc()).limit(limit).all()

        if not assets:
            print(f"  ℹ️  No assets found" +
                  (f" of type '{asset_type}'" if asset_type else ""))
            return

        print(f"  📦 Asset Registry — Assets ({len(assets)})\n")
        for a in assets:
            _print_asset(a)
    finally:
        session.close()


def cmd_lineage(asset_id: str) -> None:
    session = get_sync_session()
    try:
        asset = session.query(AssetRecord).filter(AssetRecord.id == asset_id).first()
        if not asset:
            print(f"  ❌ Asset not found: {asset_id}")
            return

        print(f"\n  🔗 Asset Lineage — {asset.id}")
        print(f"  {'=' * 50}")

        # ── Current asset ──
        print(f"\n  📄 Current Asset")
        print(f"    type:      {asset.asset_type}")
        print(f"    path:      {asset.path or '—'}")
        print(f"    summary:   {asset.summary or '—'}")
        print(f"    status:    {asset.status}")
        print(f"    created:   {asset.created_at}")

        # ── Source chain ──
        sources = []
        if asset.source_brief:
            sources.append(("CEO Brief", asset.source_brief))
        if asset.source_decision:
            sources.append(("Decision", asset.source_decision))
        if asset.source_draft:
            sources.append(("Draft", asset.source_draft))
        if asset.source_work_order:
            sources.append(("Work Order", asset.source_work_order))

        if sources:
            print(f"\n  ⬆ Source Chain")
            for label, val in sources:
                print(f"    {label:<15} {val}")

        # ── Related ledger events ──
        events = session.query(RunLedgerEvent).filter(
            RunLedgerEvent.asset_id == asset_id
        ).order_by(RunLedgerEvent.timestamp.asc()).all()

        if events:
            print(f"\n  📋 Related Events ({len(events)})")
            for evt in events:
                print(f"    [{evt.event_type}] {evt.timestamp} — {evt.summary or '—'}")

        # ── Child assets (this asset is a source for) ──
        children = session.query(AssetRecord).filter(
            (AssetRecord.source_brief == asset.path) |
            (AssetRecord.source_decision == asset.source_decision) |
            (AssetRecord.source_draft == asset.source_draft) |
            (AssetRecord.source_work_order == asset.source_work_order)
        ).filter(AssetRecord.id != asset_id).all()

        if children:
            print(f"\n  ⬇ Derived Assets ({len(children)})")
            for c in children:
                print(f"    [{c.asset_type}] {c.id} — {c.summary or c.path or '—'}")

        print()
    finally:
        session.close()


# ── Main ──────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="v0.23 — OS Registry: Run Ledger & Asset Registry CLI"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ledger
    ledger_p = subparsers.add_parser("ledger", help="Query Run Ledger events")
    ledger_sub = ledger_p.add_subparsers(dest="subcommand", required=True)
    recent_p = ledger_sub.add_parser("recent", help="List recent events")
    recent_p.add_argument("--limit", type=int, default=20, help="Max events (default: 20)")
    recent_p.add_argument("--type", dest="event_type", default="", help="Filter by event type")

    # assets
    assets_p = subparsers.add_parser("assets", help="Query Asset Registry")
    assets_sub = assets_p.add_subparsers(dest="subcommand", required=True)
    list_p = assets_sub.add_parser("list", help="List assets")
    list_p.add_argument("--type", dest="asset_type", default="", help="Filter by asset type")
    list_p.add_argument("--limit", type=int, default=20, help="Max assets (default: 20)")

    # lineage
    lineage_p = subparsers.add_parser("lineage", help="Show asset lineage")
    lineage_p.add_argument("asset_id", help="Asset ID (e.g. ast-XXXX)")

    args = parser.parse_args()

    if args.command == "ledger":
        if args.subcommand == "recent":
            cmd_ledger_recent(limit=args.limit, event_type=args.event_type)
    elif args.command == "assets":
        if args.subcommand == "list":
            cmd_assets_list(asset_type=args.asset_type, limit=args.limit)
    elif args.command == "lineage":
        cmd_lineage(args.asset_id)


if __name__ == "__main__":
    main()
