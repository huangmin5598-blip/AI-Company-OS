# @PRODUCT Model — OS Core
"""Run Ledger Event — append-only OS-level event log.

Records every key event in the AI Company OS pipeline:
  brief_generated → review_created → decision_logged → draft_created
  → work_order_created → approved_for_dispatch → work_order_routed
  → work_order_executed → callback_completed → result_synced

Idempotent: unique constraint on (event_type, source_id, work_order_id).
"""
from sqlalchemy import Column, String, Text, Integer, UniqueConstraint
from sqlalchemy import Index
from app.models.base import Base


class RunLedgerEvent(Base):
    __tablename__ = "run_ledger_events"

    id = Column(String, primary_key=True)
    event_type = Column(String, nullable=False)
    source_type = Column(String, default="")
    source_id = Column(String, default="")
    work_order_id = Column(String, default="")
    decision_id = Column(String, default="")
    draft_id = Column(String, default="")
    asset_id = Column(String, default="")
    actor = Column(String, default="system")
    timestamp = Column(String, nullable=False)
    summary = Column(String, default="")
    metadata_json = Column(Text, default="")

    __table_args__ = (
        UniqueConstraint(
            "event_type", "source_id", "work_order_id",
            name="uix_ledger_event_dedup",
        ),
        Index("idx_ledger_event_type", "event_type"),
        Index("idx_ledger_timestamp", "timestamp"),
        Index("idx_ledger_wo_id", "work_order_id"),
    )
