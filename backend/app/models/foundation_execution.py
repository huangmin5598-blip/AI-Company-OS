"""Canonical execution, governance, promotion, and migration-preparation models."""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.sql import func

from app.models.foundation_base import FoundationBase


ATTEMPT_STATES = (
    "created",
    "claimed",
    "running",
    "cancellation_requested",
    "succeeded",
    "failed",
    "timed_out",
    "cancelled",
    "stale",
)
ACTIVE_ATTEMPT_STATES = ("claimed", "running", "cancellation_requested")
APPROVAL_DECISIONS = ("requested", "approved", "rejected", "withdrawn")
REVIEW_STATES = (
    "requested",
    "in_review",
    "blocked",
    "passed",
    "revision_required",
    "failed",
    "cancelled",
)
MIGRATION_CLASSIFICATIONS = (
    "high_confidence",
    "provisional",
    "ambiguous",
    "conflicting",
    "noncanonical_history",
    "orphaned",
)


class PromotionRecord(FoundationBase):
    __tablename__ = "promotion_records"

    promotion_id = Column(String(64), primary_key=True)
    promotion_key = Column(String(80), nullable=False, unique=True)
    tenant_id = Column(
        String(64),
        ForeignKey("tenants.tenant_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    workspace_id = Column(
        String(64),
        ForeignKey("workspaces.workspace_id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    scope_key = Column(String(160), nullable=False)
    intake_id = Column(String(160), nullable=False)
    source_conversation_ref = Column(String(500), nullable=False)
    source_provider = Column(String(120), nullable=False)
    source_domain = Column(String(80), nullable=False, default="general")
    original_mode = Column(String(32), nullable=False)
    promoted_mode = Column(String(32), nullable=False)
    promoted_by = Column(String(64), nullable=False)
    promoted_at = Column(DateTime(timezone=True), nullable=False)
    promotion_rationale = Column(Text, nullable=False)
    target_object_type = Column(String(80), nullable=False)
    target_work_order_id = Column(String(160), nullable=True, index=True)
    target_project_id = Column(String(160), nullable=True)
    accepted_context_refs_json = Column(Text, nullable=False, default="[]")
    rejected_context_refs_json = Column(Text, nullable=False, default="[]")
    review_required = Column(Boolean, nullable=False, default=True)
    audit_event_ref = Column(
        String(64),
        ForeignKey("audit_events.audit_event_id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    idempotency_ref = Column(
        String(64),
        ForeignKey(
            "idempotency_records.idempotency_record_id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        unique=True,
    )
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "original_mode = 'native'",
            name="ck_promotion_original_mode_native",
        ),
        CheckConstraint(
            "promoted_mode = 'promotion'",
            name="ck_promotion_promoted_mode",
        ),
    )


class MigrationBatch(FoundationBase):
    __tablename__ = "migration_batches"

    migration_batch_id = Column(String(64), primary_key=True)
    source_manifest_hash = Column(String(80), nullable=False)
    ruleset_version = Column(String(80), nullable=False)
    mode = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False)
    counts_json = Column(Text, nullable=False, default="{}")
    report_ref = Column(String(500), nullable=True)
    created_by = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "mode IN ('dry_run', 'apply')",
            name="ck_migration_batch_mode",
        ),
    )


class WorkAttempt(FoundationBase):
    __tablename__ = "work_attempts"

    attempt_id = Column(String(64), primary_key=True)
    tenant_id = Column(
        String(64),
        ForeignKey("tenants.tenant_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    workspace_id = Column(
        String(64),
        ForeignKey("workspaces.workspace_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    scope_key = Column(String(160), nullable=False)
    work_order_id = Column(String(160), nullable=False, index=True)
    attempt_number = Column(Integer, nullable=False)
    parent_attempt_id = Column(
        String(64),
        ForeignKey("work_attempts.attempt_id", ondelete="RESTRICT"),
        nullable=True,
    )
    trigger_reason = Column(String(64), nullable=False)
    state = Column(String(32), nullable=False)
    row_version = Column(Integer, nullable=False, default=1)
    runtime_adapter_id = Column(String(160), nullable=False)
    runtime_adapter_version = Column(String(80), nullable=False)
    runtime_config_snapshot_json = Column(Text, nullable=False)
    runtime_session_id = Column(String(240), nullable=True, index=True)
    worker_id = Column(String(160), nullable=True)
    lease_owner = Column(String(160), nullable=True)
    lease_token_hash = Column(String(80), nullable=True)
    lease_generation = Column(Integer, nullable=False, default=0)
    claimed_at = Column(DateTime(timezone=True), nullable=True)
    lease_expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    heartbeat_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    soft_timeout_at = Column(DateTime(timezone=True), nullable=True)
    hard_deadline_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    invocation_authenticity_json = Column(Text, nullable=False, default="{}")
    handoff_packet_ref = Column(String(500), nullable=True)
    context_pack_snapshot_ref = Column(String(500), nullable=True)
    policy_snapshot_ref = Column(String(500), nullable=True)
    allowed_read_refs_json = Column(Text, nullable=False, default="[]")
    allowed_write_refs_json = Column(Text, nullable=False, default="[]")
    result_ref = Column(String(500), nullable=True)
    stdout_ref = Column(String(500), nullable=True)
    stderr_ref = Column(String(500), nullable=True)
    exit_code = Column(Integer, nullable=True)
    error_code = Column(String(120), nullable=True)
    error_summary = Column(Text, nullable=True)
    cost_summary_json = Column(Text, nullable=True)
    result_idempotency_key = Column(String(240), nullable=True)
    result_payload_hash = Column(String(80), nullable=True)
    created_by = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    migration_batch_id = Column(
        String(64),
        ForeignKey("migration_batches.migration_batch_id", ondelete="RESTRICT"),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "work_order_id",
            "attempt_number",
            name="uq_work_attempt_number",
        ),
        CheckConstraint(
            f"state IN {ATTEMPT_STATES}",
            name="ck_work_attempt_state",
        ),
        CheckConstraint("attempt_number >= 1", name="ck_work_attempt_number_positive"),
        CheckConstraint("row_version >= 1", name="ck_work_attempt_row_version"),
        CheckConstraint(
            "lease_generation >= 0",
            name="ck_work_attempt_lease_generation",
        ),
        Index(
            "uq_work_attempt_active",
            "work_order_id",
            unique=True,
            sqlite_where=text(
                "state IN ('claimed','running','cancellation_requested')"
            ),
            postgresql_where=text(
                "state IN ('claimed','running','cancellation_requested')"
            ),
        ),
        Index("ix_work_attempt_order_state", "work_order_id", "state"),
        Index("ix_work_attempt_state_lease", "state", "lease_expires_at"),
        Index(
            "uq_work_attempt_result_idempotency",
            "scope_key",
            "result_idempotency_key",
            unique=True,
            sqlite_where=text("result_idempotency_key IS NOT NULL"),
            postgresql_where=text("result_idempotency_key IS NOT NULL"),
        ),
    )


class WorkApproval(FoundationBase):
    __tablename__ = "work_approvals"

    approval_id = Column(String(64), primary_key=True)
    tenant_id = Column(
        String(64),
        ForeignKey("tenants.tenant_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    workspace_id = Column(
        String(64),
        ForeignKey("workspaces.workspace_id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    scope_key = Column(String(160), nullable=False)
    target_type = Column(String(80), nullable=False)
    target_id = Column(String(160), nullable=False)
    target_version = Column(String(80), nullable=False)
    action = Column(String(160), nullable=False)
    risk_level = Column(String(32), nullable=False)
    requested_by = Column(String(64), nullable=False)
    requested_at = Column(DateTime(timezone=True), nullable=False)
    decision = Column(String(32), nullable=False, default="requested")
    decided_by = Column(String(64), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    conditions_json = Column(Text, nullable=False, default="[]")
    decision_note = Column(Text, nullable=True)
    context_snapshot_ref = Column(String(500), nullable=True)
    supersedes_approval_id = Column(
        String(64),
        ForeignKey("work_approvals.approval_id", ondelete="RESTRICT"),
        nullable=True,
    )
    row_version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            f"decision IN {APPROVAL_DECISIONS}",
            name="ck_work_approval_decision",
        ),
        CheckConstraint("row_version >= 1", name="ck_work_approval_row_version"),
    )


class WorkReview(FoundationBase):
    __tablename__ = "work_reviews"

    review_id = Column(String(64), primary_key=True)
    tenant_id = Column(
        String(64),
        ForeignKey("tenants.tenant_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    workspace_id = Column(
        String(64),
        ForeignKey("workspaces.workspace_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    scope_key = Column(String(160), nullable=False)
    work_order_id = Column(String(160), nullable=False, index=True)
    attempt_id = Column(
        String(64),
        ForeignKey("work_attempts.attempt_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    state = Column(String(32), nullable=False, default="requested")
    review_type = Column(String(80), nullable=False)
    reviewer_type = Column(String(64), nullable=True)
    reviewer_id = Column(String(64), nullable=True)
    artifact_ids_json = Column(Text, nullable=False, default="[]")
    criteria_snapshot_json = Column(Text, nullable=False)
    findings_json = Column(Text, nullable=False, default="[]")
    required_revisions_json = Column(Text, nullable=False, default="[]")
    next_action = Column(String(160), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    supersedes_review_id = Column(
        String(64),
        ForeignKey("work_reviews.review_id", ondelete="RESTRICT"),
        nullable=True,
    )
    row_version = Column(Integer, nullable=False, default=1)
    created_by = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            f"state IN {REVIEW_STATES}",
            name="ck_work_review_state",
        ),
        CheckConstraint("row_version >= 1", name="ck_work_review_row_version"),
    )


class LegacyMapping(FoundationBase):
    __tablename__ = "legacy_mappings"

    legacy_mapping_id = Column(String(64), primary_key=True)
    source_system = Column(String(120), nullable=False)
    source_type = Column(String(120), nullable=False)
    source_key = Column(String(240), nullable=False)
    source_state = Column(String(120), nullable=True)
    source_hash = Column(String(80), nullable=False)
    canonical_object_type = Column(String(80), nullable=True)
    canonical_object_id = Column(String(160), nullable=True)
    classification = Column(String(40), nullable=False)
    mapping_rule = Column(String(160), nullable=False)
    migration_batch_id = Column(
        String(64),
        ForeignKey("migration_batches.migration_batch_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "source_system",
            "source_type",
            "source_key",
            name="uq_legacy_mapping_source",
        ),
        CheckConstraint(
            f"classification IN {MIGRATION_CLASSIFICATIONS}",
            name="ck_legacy_mapping_classification",
        ),
    )


class ReconciliationAnomaly(FoundationBase):
    __tablename__ = "reconciliation_anomalies"

    anomaly_id = Column(String(64), primary_key=True)
    migration_batch_id = Column(
        String(64),
        ForeignKey("migration_batches.migration_batch_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    tenant_id = Column(String(64), nullable=True, index=True)
    workspace_id = Column(String(64), nullable=True, index=True)
    source_system = Column(String(120), nullable=False)
    source_type = Column(String(120), nullable=False)
    source_key = Column(String(240), nullable=False)
    anomaly_type = Column(String(80), nullable=False)
    severity = Column(String(32), nullable=False)
    details_json = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="open")
    resolution_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
