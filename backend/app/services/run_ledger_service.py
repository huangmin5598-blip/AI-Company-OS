# @PRODUCT Service — OS Core
"""Run Ledger & Asset Registry — unified service for recording OS events and registering assets.

Two responsibilities:
  1. record_event() — append-only event log (run_ledger_events table)
  2. register_asset() — asset catalog (asset_registry table)

Both functions are idempotent. They rely on unique constraints to prevent duplicates.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.database import get_sync_session
from app.models.run_ledger_event import RunLedgerEvent
from app.models.asset_record import AssetRecord


# ── Helpers ─────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _new_id(prefix: str = "evt") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"


def _build_dedup_key(event_type: str, source_id: str, work_order_id: str = "",
                     decision_id: str = "", draft_id: str = "") -> tuple:
    """Build the dedup key based on event context.

    Layered idempotency:
      - File events (brief, review): event_type + source_id
      - WO events: event_type + source_id + work_order_id
      - Decision events: event_type + decision_id
      - Draft events: event_type + draft_id
    """
    if decision_id:
        return (event_type, "", decision_id)
    if draft_id:
        return (event_type, "", draft_id)
    if work_order_id:
        return (event_type, source_id, work_order_id)
    return (event_type, source_id, "")


# ── Public API ─────────────────────────────────────────────────────────

def record_event(
    event_type: str,
    source_type: str = "",
    source_id: str = "",
    work_order_id: str = "",
    decision_id: str = "",
    draft_id: str = "",
    asset_id: str = "",
    actor: str = "system",
    summary: str = "",
    metadata: Optional[dict] = None,
    skip_dupe: bool = True,
) -> bool:
    """Record an OS-level event. Returns True if recorded, False if skipped (duplicate).

    Args:
        event_type: One of the canonical event types (brief_generated, review_created, etc.)
        source_type: e.g. 'file', 'work_order', 'decision'
        source_id: Path or identifier of the source entity
        work_order_id: WO ID if this event is WO-related
        decision_id: Decision ID if this event is decision-related
        draft_id: Draft ID if this event is draft-related
        asset_id: Associated asset ID if already registered
        actor: Who/what triggered the event
        summary: Human-readable summary
        metadata: Optional dict for additional context (JSON-serialized)
    """
    dedup_key = _build_dedup_key(event_type, source_id, work_order_id, decision_id, draft_id)
    # dedup_key tuple order matches the unique constraint ordering

    session = get_sync_session()
    try:
        # Check for existing event with same dedup signature
        if skip_dupe:
            existing = session.query(RunLedgerEvent).filter(
                RunLedgerEvent.event_type == dedup_key[0],
                RunLedgerEvent.source_id == dedup_key[1],
                RunLedgerEvent.work_order_id == dedup_key[2],
            ).first()
            if existing:
                return False

        event = RunLedgerEvent(
            id=_new_id("evt"),
            event_type=event_type,
            source_type=source_type,
            source_id=source_id,
            work_order_id=work_order_id,
            decision_id=decision_id,
            draft_id=draft_id,
            asset_id=asset_id,
            actor=actor,
            timestamp=_now(),
            summary=summary,
            metadata_json=json.dumps(metadata or {}, ensure_ascii=False),
        )
        session.add(event)
        session.commit()
        return True
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def register_asset(
    asset_type: str,
    source_id: str = "",
    path: str = "",
    source_brief: str = "",
    source_decision: str = "",
    source_draft: str = "",
    source_work_order: str = "",
    created_by: str = "system",
    summary: str = "",
    status: str = "created",
    tags: str = "",
    metadata: Optional[dict] = None,
    skip_dupe: bool = True,
) -> Optional[str]:
    """Register a company asset. Returns asset_id if registered, None if skipped (duplicate).

    Args:
        asset_type: One of: ceo_brief / ceo_brief_review / decision_log_entry /
                             work_order_draft / work_order / execution_result /
                             governance_policy / operating_kit_doc / template
        source_id: Original source path or unique identifier
        path: File path to the asset
        source_brief: Brief path this asset originated from
        source_decision: Decision ID this asset relates to
        source_draft: Draft ID this asset relates to
        source_work_order: Work Order ID this asset relates to
        created_by: Who registered this asset
        summary: Brief description
        status: Asset lifecycle status (created, completed, archived)
        tags: Comma-separated tags
        metadata: Optional dict (JSON-serialized)
        skip_dupe: If True, skip if duplicate asset exists
    """
    session = get_sync_session()
    try:
        if skip_dupe:
            existing = session.query(AssetRecord).filter(
                AssetRecord.asset_type == asset_type,
                AssetRecord.source_id == source_id,
                AssetRecord.source_work_order == source_work_order,
            ).first()
            if existing:
                return None

        asset_id = _new_id("ast")
        asset = AssetRecord(
            id=asset_id,
            asset_type=asset_type,
            source_id=source_id,
            path=path,
            source_brief=source_brief,
            source_decision=source_decision,
            source_draft=source_draft,
            source_work_order=source_work_order,
            created_by=created_by,
            created_at=_now(),
            summary=summary,
            status=status,
            tags=tags,
            metadata_json=json.dumps(metadata or {}, ensure_ascii=False),
        )
        session.add(asset)
        session.commit()
        return asset_id
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def record_and_register(
    event_type: str,
    asset_type: str,
    source_type: str = "",
    source_id: str = "",
    path: str = "",
    work_order_id: str = "",
    decision_id: str = "",
    draft_id: str = "",
    actor: str = "system",
    summary: str = "",
    source_brief: str = "",
    source_decision: str = "",
    source_draft: str = "",
    source_work_order: str = "",
    tags: str = "",
    metadata: Optional[dict] = None,
) -> dict:
    """Convenience: record an event AND register an asset in one call.

    Returns {'event_recorded': bool, 'asset_id': str|None, 'asset_registered': bool}.
    """
    event_recorded = record_event(
        event_type=event_type,
        source_type=source_type,
        source_id=source_id,
        work_order_id=work_order_id,
        decision_id=decision_id,
        draft_id=draft_id,
        actor=actor,
        summary=summary,
        metadata=metadata,
    )

    asset_id = register_asset(
        asset_type=asset_type,
        source_id=source_id,
        path=path or source_id,
        source_brief=source_brief or source_id if asset_type == "ceo_brief" else source_brief,
        source_decision=source_decision or decision_id,
        source_draft=source_draft or draft_id,
        source_work_order=source_work_order or work_order_id,
        created_by=actor,
        summary=summary,
        tags=tags,
        metadata=metadata,
    )

    return {
        "event_recorded": event_recorded,
        "asset_id": asset_id,
        "asset_registered": asset_id is not None,
    }
