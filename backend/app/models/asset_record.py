"""
Asset Record — registry of company assets produced by the OS pipeline.

First-pass asset types:
  ceo_brief / ceo_brief_review / decision_log_entry
  work_order_draft / work_order / execution_result

v0.27 added:
  governance_policy / operating_kit_doc / template

Idempotent: unique constraint on (asset_type, source_id, source_work_order).
"""
from sqlalchemy import Column, String, Text, UniqueConstraint, Index
from app.models.base import Base


class AssetRecord(Base):
    __tablename__ = "asset_registry"

    id = Column(String, primary_key=True)
    asset_type = Column(String, nullable=False)
    source_id = Column(String, default="")
    path = Column(String, default="")
    source_brief = Column(String, default="")
    source_decision = Column(String, default="")
    source_draft = Column(String, default="")
    source_work_order = Column(String, default="")
    created_by = Column(String, default="system")
    created_at = Column(String, nullable=False)
    summary = Column(String, default="")
    status = Column(String, default="created")
    tags = Column(String, default="")
    metadata_json = Column(Text, default="")

    __table_args__ = (
        UniqueConstraint(
            "asset_type", "source_id", "source_work_order",
            name="uix_asset_dedup",
        ),
        Index("idx_asset_type", "asset_type"),
        Index("idx_asset_created_at", "created_at"),
    )
