"""Add promotion and canonical execution persistence preparation.

Revision ID: 0003_promotion_execution_persistence
Revises: 0002_identity_scope_audit
Create Date: 2026-06-07
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0003_promotion_execution_persistence"
down_revision: str | None = "0002_identity_scope_audit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


WORK_ORDER_COLUMN_NAMES = (
    "tenant_id",
    "workspace_id",
    "created_by",
    "updated_by",
    "visibility",
    "canonical_state",
    "row_version",
    "parallel_attempts_allowed",
    "max_attempts",
    "canonicalized_at",
    "canonical_migration_batch_id",
    "legacy_status_snapshot",
    "terminal_at",
)


def _work_order_columns() -> tuple[sa.Column, ...]:
    return (
        sa.Column("tenant_id", sa.String(length=64), nullable=True),
        sa.Column("workspace_id", sa.String(length=64), nullable=True),
        sa.Column("created_by", sa.String(length=64), nullable=True),
        sa.Column("updated_by", sa.String(length=64), nullable=True),
        sa.Column("visibility", sa.String(length=32), nullable=True),
        sa.Column("canonical_state", sa.String(length=32), nullable=True),
        sa.Column("row_version", sa.Integer(), nullable=True),
        sa.Column("parallel_attempts_allowed", sa.Boolean(), nullable=True),
        sa.Column("max_attempts", sa.Integer(), nullable=True),
        sa.Column("canonicalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "canonical_migration_batch_id",
            sa.String(length=64),
            nullable=True,
        ),
        sa.Column("legacy_status_snapshot", sa.String(length=120), nullable=True),
        sa.Column("terminal_at", sa.DateTime(timezone=True), nullable=True),
    )


def _table_exists(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def _column_names(table_name: str) -> set[str]:
    return {
        column["name"]
        for column in sa.inspect(op.get_bind()).get_columns(table_name)
    }


def _add_work_order_support_columns() -> None:
    if not _table_exists("work_orders"):
        return
    existing = _column_names("work_orders")
    with op.batch_alter_table("work_orders") as batch:
        for column in _work_order_columns():
            if column.name not in existing:
                batch.add_column(column)


def _drop_work_order_support_columns() -> None:
    if not _table_exists("work_orders"):
        return
    existing = _column_names("work_orders")
    with op.batch_alter_table("work_orders") as batch:
        for column_name in reversed(WORK_ORDER_COLUMN_NAMES):
            if column_name in existing:
                batch.drop_column(column_name)


def upgrade() -> None:
    op.create_table(
        "migration_batches",
        sa.Column("migration_batch_id", sa.String(length=64), primary_key=True),
        sa.Column("source_manifest_hash", sa.String(length=80), nullable=False),
        sa.Column("ruleset_version", sa.String(length=80), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "counts_json",
            sa.Text(),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("report_ref", sa.String(length=500), nullable=True),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "mode IN ('dry_run', 'apply')",
            name="ck_migration_batch_mode",
        ),
    )
    op.create_table(
        "promotion_records",
        sa.Column("promotion_id", sa.String(length=64), primary_key=True),
        sa.Column("promotion_key", sa.String(length=80), nullable=False),
        sa.Column(
            "tenant_id",
            sa.String(length=64),
            sa.ForeignKey("tenants.tenant_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            sa.String(length=64),
            sa.ForeignKey("workspaces.workspace_id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("scope_key", sa.String(length=160), nullable=False),
        sa.Column("intake_id", sa.String(length=160), nullable=False),
        sa.Column(
            "source_conversation_ref",
            sa.String(length=500),
            nullable=False,
        ),
        sa.Column("source_provider", sa.String(length=120), nullable=False),
        sa.Column(
            "source_domain",
            sa.String(length=80),
            nullable=False,
            server_default="general",
        ),
        sa.Column("original_mode", sa.String(length=32), nullable=False),
        sa.Column("promoted_mode", sa.String(length=32), nullable=False),
        sa.Column("promoted_by", sa.String(length=64), nullable=False),
        sa.Column("promoted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("promotion_rationale", sa.Text(), nullable=False),
        sa.Column("target_object_type", sa.String(length=80), nullable=False),
        sa.Column("target_work_order_id", sa.String(length=160), nullable=True),
        sa.Column("target_project_id", sa.String(length=160), nullable=True),
        sa.Column(
            "accepted_context_refs_json",
            sa.Text(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "rejected_context_refs_json",
            sa.Text(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "review_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "audit_event_ref",
            sa.String(length=64),
            sa.ForeignKey("audit_events.audit_event_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "idempotency_ref",
            sa.String(length=64),
            sa.ForeignKey(
                "idempotency_records.idempotency_record_id",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.UniqueConstraint("promotion_key", name="uq_promotion_key"),
        sa.UniqueConstraint("audit_event_ref", name="uq_promotion_audit_event"),
        sa.UniqueConstraint("idempotency_ref", name="uq_promotion_idempotency"),
        sa.CheckConstraint(
            "original_mode = 'native'",
            name="ck_promotion_original_mode_native",
        ),
        sa.CheckConstraint(
            "promoted_mode = 'promotion'",
            name="ck_promotion_promoted_mode",
        ),
    )
    op.create_index(
        "ix_promotion_records_tenant_id",
        "promotion_records",
        ["tenant_id"],
    )
    op.create_index(
        "ix_promotion_records_workspace_id",
        "promotion_records",
        ["workspace_id"],
    )
    op.create_index(
        "ix_promotion_records_target_work_order_id",
        "promotion_records",
        ["target_work_order_id"],
    )
    op.create_table(
        "work_attempts",
        sa.Column("attempt_id", sa.String(length=64), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.String(length=64),
            sa.ForeignKey("tenants.tenant_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            sa.String(length=64),
            sa.ForeignKey("workspaces.workspace_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("scope_key", sa.String(length=160), nullable=False),
        sa.Column("work_order_id", sa.String(length=160), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column(
            "parent_attempt_id",
            sa.String(length=64),
            sa.ForeignKey("work_attempts.attempt_id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("trigger_reason", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("row_version", sa.Integer(), nullable=False),
        sa.Column("runtime_adapter_id", sa.String(length=160), nullable=False),
        sa.Column("runtime_adapter_version", sa.String(length=80), nullable=False),
        sa.Column("runtime_config_snapshot_json", sa.Text(), nullable=False),
        sa.Column("runtime_session_id", sa.String(length=240), nullable=True),
        sa.Column("worker_id", sa.String(length=160), nullable=True),
        sa.Column("lease_owner", sa.String(length=160), nullable=True),
        sa.Column("lease_token_hash", sa.String(length=80), nullable=True),
        sa.Column("lease_generation", sa.Integer(), nullable=False),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("soft_timeout_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("hard_deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "invocation_authenticity_json",
            sa.Text(),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("handoff_packet_ref", sa.String(length=500), nullable=True),
        sa.Column(
            "context_pack_snapshot_ref",
            sa.String(length=500),
            nullable=True,
        ),
        sa.Column("policy_snapshot_ref", sa.String(length=500), nullable=True),
        sa.Column(
            "allowed_read_refs_json",
            sa.Text(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "allowed_write_refs_json",
            sa.Text(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("result_ref", sa.String(length=500), nullable=True),
        sa.Column("stdout_ref", sa.String(length=500), nullable=True),
        sa.Column("stderr_ref", sa.String(length=500), nullable=True),
        sa.Column("exit_code", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=120), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("cost_summary_json", sa.Text(), nullable=True),
        sa.Column("result_idempotency_key", sa.String(length=240), nullable=True),
        sa.Column("result_payload_hash", sa.String(length=80), nullable=True),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column(
            "migration_batch_id",
            sa.String(length=64),
            sa.ForeignKey(
                "migration_batches.migration_batch_id",
                ondelete="RESTRICT",
            ),
            nullable=True,
        ),
        sa.UniqueConstraint(
            "work_order_id",
            "attempt_number",
            name="uq_work_attempt_number",
        ),
        sa.CheckConstraint(
            "state IN ('created','claimed','running','cancellation_requested',"
            "'succeeded','failed','timed_out','cancelled','stale')",
            name="ck_work_attempt_state",
        ),
        sa.CheckConstraint(
            "attempt_number >= 1",
            name="ck_work_attempt_number_positive",
        ),
        sa.CheckConstraint("row_version >= 1", name="ck_work_attempt_row_version"),
        sa.CheckConstraint(
            "lease_generation >= 0",
            name="ck_work_attempt_lease_generation",
        ),
    )
    op.create_index("ix_work_attempts_tenant_id", "work_attempts", ["tenant_id"])
    op.create_index(
        "ix_work_attempts_workspace_id",
        "work_attempts",
        ["workspace_id"],
    )
    op.create_index(
        "ix_work_attempts_work_order_id",
        "work_attempts",
        ["work_order_id"],
    )
    op.create_index(
        "ix_work_attempts_runtime_session_id",
        "work_attempts",
        ["runtime_session_id"],
    )
    op.create_index(
        "ix_work_attempts_lease_expires_at",
        "work_attempts",
        ["lease_expires_at"],
    )
    op.create_index(
        "ix_work_attempt_order_state",
        "work_attempts",
        ["work_order_id", "state"],
    )
    op.create_index(
        "ix_work_attempt_state_lease",
        "work_attempts",
        ["state", "lease_expires_at"],
    )
    op.create_index(
        "uq_work_attempt_active",
        "work_attempts",
        ["work_order_id"],
        unique=True,
        sqlite_where=sa.text(
            "state IN ('claimed','running','cancellation_requested')"
        ),
        postgresql_where=sa.text(
            "state IN ('claimed','running','cancellation_requested')"
        ),
    )
    op.create_index(
        "uq_work_attempt_result_idempotency",
        "work_attempts",
        ["scope_key", "result_idempotency_key"],
        unique=True,
        sqlite_where=sa.text("result_idempotency_key IS NOT NULL"),
        postgresql_where=sa.text("result_idempotency_key IS NOT NULL"),
    )
    op.create_table(
        "work_approvals",
        sa.Column("approval_id", sa.String(length=64), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.String(length=64),
            sa.ForeignKey("tenants.tenant_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            sa.String(length=64),
            sa.ForeignKey("workspaces.workspace_id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("scope_key", sa.String(length=160), nullable=False),
        sa.Column("target_type", sa.String(length=80), nullable=False),
        sa.Column("target_id", sa.String(length=160), nullable=False),
        sa.Column("target_version", sa.String(length=80), nullable=False),
        sa.Column("action", sa.String(length=160), nullable=False),
        sa.Column("risk_level", sa.String(length=32), nullable=False),
        sa.Column("requested_by", sa.String(length=64), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("decided_by", sa.String(length=64), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "conditions_json",
            sa.Text(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("decision_note", sa.Text(), nullable=True),
        sa.Column("context_snapshot_ref", sa.String(length=500), nullable=True),
        sa.Column(
            "supersedes_approval_id",
            sa.String(length=64),
            sa.ForeignKey("work_approvals.approval_id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("row_version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.CheckConstraint(
            "decision IN ('requested','approved','rejected','withdrawn')",
            name="ck_work_approval_decision",
        ),
        sa.CheckConstraint(
            "row_version >= 1",
            name="ck_work_approval_row_version",
        ),
    )
    op.create_index(
        "ix_work_approvals_tenant_id",
        "work_approvals",
        ["tenant_id"],
    )
    op.create_index(
        "ix_work_approvals_workspace_id",
        "work_approvals",
        ["workspace_id"],
    )
    op.create_table(
        "work_reviews",
        sa.Column("review_id", sa.String(length=64), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.String(length=64),
            sa.ForeignKey("tenants.tenant_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            sa.String(length=64),
            sa.ForeignKey("workspaces.workspace_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("scope_key", sa.String(length=160), nullable=False),
        sa.Column("work_order_id", sa.String(length=160), nullable=False),
        sa.Column(
            "attempt_id",
            sa.String(length=64),
            sa.ForeignKey("work_attempts.attempt_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("review_type", sa.String(length=80), nullable=False),
        sa.Column("reviewer_type", sa.String(length=64), nullable=True),
        sa.Column("reviewer_id", sa.String(length=64), nullable=True),
        sa.Column(
            "artifact_ids_json",
            sa.Text(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("criteria_snapshot_json", sa.Text(), nullable=False),
        sa.Column(
            "findings_json",
            sa.Text(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "required_revisions_json",
            sa.Text(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("next_action", sa.String(length=160), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "supersedes_review_id",
            sa.String(length=64),
            sa.ForeignKey("work_reviews.review_id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("row_version", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.CheckConstraint(
            "state IN ('requested','in_review','blocked','passed',"
            "'revision_required','failed','cancelled')",
            name="ck_work_review_state",
        ),
        sa.CheckConstraint("row_version >= 1", name="ck_work_review_row_version"),
    )
    op.create_index("ix_work_reviews_tenant_id", "work_reviews", ["tenant_id"])
    op.create_index(
        "ix_work_reviews_workspace_id",
        "work_reviews",
        ["workspace_id"],
    )
    op.create_index(
        "ix_work_reviews_work_order_id",
        "work_reviews",
        ["work_order_id"],
    )
    op.create_index("ix_work_reviews_attempt_id", "work_reviews", ["attempt_id"])
    op.create_table(
        "legacy_mappings",
        sa.Column("legacy_mapping_id", sa.String(length=64), primary_key=True),
        sa.Column("source_system", sa.String(length=120), nullable=False),
        sa.Column("source_type", sa.String(length=120), nullable=False),
        sa.Column("source_key", sa.String(length=240), nullable=False),
        sa.Column("source_state", sa.String(length=120), nullable=True),
        sa.Column("source_hash", sa.String(length=80), nullable=False),
        sa.Column("canonical_object_type", sa.String(length=80), nullable=True),
        sa.Column("canonical_object_id", sa.String(length=160), nullable=True),
        sa.Column("classification", sa.String(length=40), nullable=False),
        sa.Column("mapping_rule", sa.String(length=160), nullable=False),
        sa.Column(
            "migration_batch_id",
            sa.String(length=64),
            sa.ForeignKey(
                "migration_batches.migration_batch_id",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.UniqueConstraint(
            "source_system",
            "source_type",
            "source_key",
            name="uq_legacy_mapping_source",
        ),
        sa.CheckConstraint(
            "classification IN ('high_confidence','provisional','ambiguous',"
            "'conflicting','noncanonical_history','orphaned')",
            name="ck_legacy_mapping_classification",
        ),
    )
    op.create_index(
        "ix_legacy_mappings_migration_batch_id",
        "legacy_mappings",
        ["migration_batch_id"],
    )
    op.create_table(
        "reconciliation_anomalies",
        sa.Column("anomaly_id", sa.String(length=64), primary_key=True),
        sa.Column(
            "migration_batch_id",
            sa.String(length=64),
            sa.ForeignKey(
                "migration_batches.migration_batch_id",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
        sa.Column("tenant_id", sa.String(length=64), nullable=True),
        sa.Column("workspace_id", sa.String(length=64), nullable=True),
        sa.Column("source_system", sa.String(length=120), nullable=False),
        sa.Column("source_type", sa.String(length=120), nullable=False),
        sa.Column("source_key", sa.String(length=240), nullable=False),
        sa.Column("anomaly_type", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="open",
        ),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_reconciliation_anomalies_migration_batch_id",
        "reconciliation_anomalies",
        ["migration_batch_id"],
    )
    op.create_index(
        "ix_reconciliation_anomalies_tenant_id",
        "reconciliation_anomalies",
        ["tenant_id"],
    )
    op.create_index(
        "ix_reconciliation_anomalies_workspace_id",
        "reconciliation_anomalies",
        ["workspace_id"],
    )

    for trigger in (
        """
        CREATE TRIGGER promotion_records_no_update
        BEFORE UPDATE ON promotion_records
        BEGIN SELECT RAISE(ABORT, 'promotion_records_append_only'); END
        """,
        """
        CREATE TRIGGER promotion_records_no_delete
        BEFORE DELETE ON promotion_records
        BEGIN SELECT RAISE(ABORT, 'promotion_records_append_only'); END
        """,
        """
        CREATE TRIGGER work_attempts_no_delete
        BEFORE DELETE ON work_attempts
        BEGIN SELECT RAISE(ABORT, 'work_attempts_history_required'); END
        """,
        """
        CREATE TRIGGER work_attempts_terminal_no_update
        BEFORE UPDATE ON work_attempts
        WHEN OLD.state IN ('succeeded','failed','timed_out','cancelled','stale')
        BEGIN SELECT RAISE(ABORT, 'work_attempt_terminal_immutable'); END
        """,
        """
        CREATE TRIGGER work_approvals_no_delete
        BEFORE DELETE ON work_approvals
        BEGIN SELECT RAISE(ABORT, 'work_approvals_history_required'); END
        """,
        """
        CREATE TRIGGER work_approvals_terminal_no_update
        BEFORE UPDATE ON work_approvals
        WHEN OLD.decision != 'requested'
        BEGIN SELECT RAISE(ABORT, 'work_approval_terminal_immutable'); END
        """,
        """
        CREATE TRIGGER work_reviews_no_delete
        BEFORE DELETE ON work_reviews
        BEGIN SELECT RAISE(ABORT, 'work_reviews_history_required'); END
        """,
        """
        CREATE TRIGGER work_reviews_terminal_no_update
        BEFORE UPDATE ON work_reviews
        WHEN OLD.state IN ('passed','revision_required','failed','cancelled')
        BEGIN SELECT RAISE(ABORT, 'work_review_terminal_immutable'); END
        """,
        """
        CREATE TRIGGER legacy_mappings_no_update
        BEFORE UPDATE ON legacy_mappings
        BEGIN SELECT RAISE(ABORT, 'legacy_mappings_append_only'); END
        """,
        """
        CREATE TRIGGER legacy_mappings_no_delete
        BEFORE DELETE ON legacy_mappings
        BEGIN SELECT RAISE(ABORT, 'legacy_mappings_append_only'); END
        """,
    ):
        op.execute(trigger)

    _add_work_order_support_columns()


def downgrade() -> None:
    _drop_work_order_support_columns()
    for trigger_name in (
        "legacy_mappings_no_delete",
        "legacy_mappings_no_update",
        "work_reviews_terminal_no_update",
        "work_reviews_no_delete",
        "work_approvals_terminal_no_update",
        "work_approvals_no_delete",
        "work_attempts_terminal_no_update",
        "work_attempts_no_delete",
        "promotion_records_no_delete",
        "promotion_records_no_update",
    ):
        op.execute(f"DROP TRIGGER IF EXISTS {trigger_name}")

    op.drop_index(
        "ix_reconciliation_anomalies_workspace_id",
        table_name="reconciliation_anomalies",
    )
    op.drop_index(
        "ix_reconciliation_anomalies_tenant_id",
        table_name="reconciliation_anomalies",
    )
    op.drop_index(
        "ix_reconciliation_anomalies_migration_batch_id",
        table_name="reconciliation_anomalies",
    )
    op.drop_table("reconciliation_anomalies")
    op.drop_index(
        "ix_legacy_mappings_migration_batch_id",
        table_name="legacy_mappings",
    )
    op.drop_table("legacy_mappings")
    op.drop_index("ix_work_reviews_attempt_id", table_name="work_reviews")
    op.drop_index("ix_work_reviews_work_order_id", table_name="work_reviews")
    op.drop_index("ix_work_reviews_workspace_id", table_name="work_reviews")
    op.drop_index("ix_work_reviews_tenant_id", table_name="work_reviews")
    op.drop_table("work_reviews")
    op.drop_index("ix_work_approvals_workspace_id", table_name="work_approvals")
    op.drop_index("ix_work_approvals_tenant_id", table_name="work_approvals")
    op.drop_table("work_approvals")
    op.drop_index(
        "uq_work_attempt_result_idempotency",
        table_name="work_attempts",
    )
    op.drop_index("uq_work_attempt_active", table_name="work_attempts")
    op.drop_index("ix_work_attempt_state_lease", table_name="work_attempts")
    op.drop_index("ix_work_attempt_order_state", table_name="work_attempts")
    op.drop_index("ix_work_attempts_lease_expires_at", table_name="work_attempts")
    op.drop_index("ix_work_attempts_runtime_session_id", table_name="work_attempts")
    op.drop_index("ix_work_attempts_work_order_id", table_name="work_attempts")
    op.drop_index("ix_work_attempts_workspace_id", table_name="work_attempts")
    op.drop_index("ix_work_attempts_tenant_id", table_name="work_attempts")
    op.drop_table("work_attempts")
    op.drop_index(
        "ix_promotion_records_target_work_order_id",
        table_name="promotion_records",
    )
    op.drop_index(
        "ix_promotion_records_workspace_id",
        table_name="promotion_records",
    )
    op.drop_index("ix_promotion_records_tenant_id", table_name="promotion_records")
    op.drop_table("promotion_records")
    op.drop_table("migration_batches")
