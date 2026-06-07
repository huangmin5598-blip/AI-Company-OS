"""Add P0 identity, scope, RBAC, idempotency, and Audit foundations.

Revision ID: 0002_identity_scope_audit
Revises: 0001_baseline
Create Date: 2026-06-07
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0002_identity_scope_audit"
down_revision: str | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("tenant_id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("updated_by", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.UniqueConstraint("slug", name="uq_tenants_slug"),
    )
    op.create_table(
        "workspaces",
        sa.Column("workspace_id", sa.String(length=64), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.String(length=64),
            sa.ForeignKey("tenants.tenant_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("updated_by", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "slug",
            name="uq_workspaces_tenant_slug",
        ),
    )
    op.create_index("ix_workspaces_tenant_id", "workspaces", ["tenant_id"])
    op.create_table(
        "users",
        sa.Column("user_id", sa.String(length=64), primary_key=True),
        sa.Column("principal_name", sa.String(length=160), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.UniqueConstraint("principal_name", name="uq_users_principal_name"),
    )
    op.create_table(
        "memberships",
        sa.Column("membership_id", sa.String(length=64), primary_key=True),
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
        sa.Column(
            "user_id",
            sa.String(length=64),
            sa.ForeignKey("users.user_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("scope_key", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.UniqueConstraint(
            "user_id",
            "scope_key",
            name="uq_memberships_user_scope",
        ),
    )
    op.create_index("ix_memberships_tenant_id", "memberships", ["tenant_id"])
    op.create_index("ix_memberships_workspace_id", "memberships", ["workspace_id"])
    op.create_index("ix_memberships_user_id", "memberships", ["user_id"])
    op.create_table(
        "roles",
        sa.Column("role_id", sa.String(length=64), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.String(length=64),
            sa.ForeignKey("tenants.tenant_id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("scope_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "name",
            "scope_type",
            name="uq_roles_tenant_name_scope",
        ),
    )
    op.create_index("ix_roles_tenant_id", "roles", ["tenant_id"])
    op.create_table(
        "permissions",
        sa.Column("permission_id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("resource", sa.String(length=80), nullable=False),
        sa.Column("command", sa.String(length=80), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.UniqueConstraint("name", name="uq_permissions_name"),
    )
    op.create_table(
        "role_permissions",
        sa.Column(
            "role_id",
            sa.String(length=64),
            sa.ForeignKey("roles.role_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "permission_id",
            sa.String(length=64),
            sa.ForeignKey("permissions.permission_id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_table(
        "membership_roles",
        sa.Column(
            "membership_id",
            sa.String(length=64),
            sa.ForeignKey("memberships.membership_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "role_id",
            sa.String(length=64),
            sa.ForeignKey("roles.role_id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_table(
        "idempotency_records",
        sa.Column(
            "idempotency_record_id",
            sa.String(length=64),
            primary_key=True,
        ),
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
        sa.Column("actor_id", sa.String(length=64), nullable=False),
        sa.Column("command", sa.String(length=160), nullable=False),
        sa.Column("target_type", sa.String(length=80), nullable=False),
        sa.Column("target_id", sa.String(length=160), nullable=False),
        sa.Column("idempotency_key", sa.String(length=240), nullable=False),
        sa.Column("request_payload_hash", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("response_ref", sa.String(length=500), nullable=True),
        sa.Column("response_hash", sa.String(length=80), nullable=True),
        sa.Column("correlation_id", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "scope_key",
            "actor_id",
            "command",
            "target_type",
            "target_id",
            "idempotency_key",
            name="uq_idempotency_command_scope",
        ),
    )
    op.create_index(
        "ix_idempotency_records_tenant_id",
        "idempotency_records",
        ["tenant_id"],
    )
    op.create_index(
        "ix_idempotency_records_workspace_id",
        "idempotency_records",
        ["workspace_id"],
    )
    op.create_table(
        "audit_aggregate_sequences",
        sa.Column("sequence_id", sa.String(length=64), primary_key=True),
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
        sa.Column("aggregate_type", sa.String(length=80), nullable=False),
        sa.Column("aggregate_id", sa.String(length=160), nullable=False),
        sa.Column("last_sequence", sa.Integer(), nullable=False),
        sa.UniqueConstraint(
            "scope_key",
            "aggregate_type",
            "aggregate_id",
            name="uq_audit_aggregate_sequence",
        ),
    )
    op.create_table(
        "audit_events",
        sa.Column("audit_event_id", sa.String(length=64), primary_key=True),
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
        sa.Column("aggregate_type", sa.String(length=80), nullable=False),
        sa.Column("aggregate_id", sa.String(length=160), nullable=False),
        sa.Column("aggregate_sequence", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=160), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("occurred_at_source", sa.String(length=64), nullable=False),
        sa.Column("actor_type", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("source_type", sa.String(length=80), nullable=False),
        sa.Column("source_id", sa.String(length=240), nullable=True),
        sa.Column("correlation_id", sa.String(length=64), nullable=False),
        sa.Column("causation_id", sa.String(length=64), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("payload_ref", sa.String(length=500), nullable=True),
        sa.Column("payload_hash", sa.String(length=80), nullable=False),
        sa.Column(
            "provenance_json",
            sa.Text(),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("work_order_id", sa.String(length=160), nullable=True),
        sa.Column("attempt_id", sa.String(length=160), nullable=True),
        sa.Column("approval_id", sa.String(length=160), nullable=True),
        sa.Column("review_id", sa.String(length=160), nullable=True),
        sa.UniqueConstraint(
            "scope_key",
            "aggregate_type",
            "aggregate_id",
            "aggregate_sequence",
            name="uq_audit_event_aggregate_sequence",
        ),
    )
    op.create_index("ix_audit_events_tenant_id", "audit_events", ["tenant_id"])
    op.create_index(
        "ix_audit_events_workspace_id",
        "audit_events",
        ["workspace_id"],
    )
    op.create_index(
        "ix_audit_events_work_order_id",
        "audit_events",
        ["work_order_id"],
    )
    op.create_index("ix_audit_events_attempt_id", "audit_events", ["attempt_id"])
    op.create_table(
        "audit_packets",
        sa.Column("audit_packet_id", sa.String(length=64), primary_key=True),
        sa.Column(
            "audit_event_id",
            sa.String(length=64),
            sa.ForeignKey("audit_events.audit_event_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("actor_id", sa.String(length=64), nullable=False),
        sa.Column("actor_type", sa.String(length=64), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
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
        sa.Column("work_order_id", sa.String(length=160), nullable=True),
        sa.Column("attempt_id", sa.String(length=160), nullable=True),
        sa.Column("action_type", sa.String(length=160), nullable=False),
        sa.Column(
            "invocation_authenticity_ref",
            sa.String(length=500),
            nullable=True,
        ),
        sa.Column("result_ref", sa.String(length=500), nullable=True),
        sa.Column(
            "evidence_refs_json",
            sa.Text(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("produced_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_hash", sa.String(length=80), nullable=False),
        sa.Column("previous_event_ref", sa.String(length=64), nullable=True),
        sa.Column("reviewer_ref", sa.String(length=160), nullable=True),
        sa.Column(
            "idempotency_ref",
            sa.String(length=64),
            sa.ForeignKey(
                "idempotency_records.idempotency_record_id",
                ondelete="RESTRICT",
            ),
            nullable=True,
        ),
        sa.UniqueConstraint("audit_event_id", name="uq_audit_packets_event"),
    )
    op.create_index("ix_audit_packets_tenant_id", "audit_packets", ["tenant_id"])
    op.create_index(
        "ix_audit_packets_workspace_id",
        "audit_packets",
        ["workspace_id"],
    )
    op.create_index(
        "ix_audit_packets_idempotency_ref",
        "audit_packets",
        ["idempotency_ref"],
    )

    op.execute(
        """
        CREATE TRIGGER audit_events_no_update
        BEFORE UPDATE ON audit_events
        BEGIN
            SELECT RAISE(ABORT, 'audit_events_append_only');
        END
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_events_no_delete
        BEFORE DELETE ON audit_events
        BEGIN
            SELECT RAISE(ABORT, 'audit_events_append_only');
        END
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_packets_no_update
        BEFORE UPDATE ON audit_packets
        BEGIN
            SELECT RAISE(ABORT, 'audit_packets_append_only');
        END
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_packets_no_delete
        BEFORE DELETE ON audit_packets
        BEGIN
            SELECT RAISE(ABORT, 'audit_packets_append_only');
        END
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_packets_no_delete")
    op.execute("DROP TRIGGER IF EXISTS audit_packets_no_update")
    op.execute("DROP TRIGGER IF EXISTS audit_events_no_delete")
    op.execute("DROP TRIGGER IF EXISTS audit_events_no_update")
    op.drop_index("ix_audit_packets_idempotency_ref", table_name="audit_packets")
    op.drop_index("ix_audit_packets_workspace_id", table_name="audit_packets")
    op.drop_index("ix_audit_packets_tenant_id", table_name="audit_packets")
    op.drop_table("audit_packets")
    op.drop_index("ix_audit_events_attempt_id", table_name="audit_events")
    op.drop_index("ix_audit_events_work_order_id", table_name="audit_events")
    op.drop_index("ix_audit_events_workspace_id", table_name="audit_events")
    op.drop_index("ix_audit_events_tenant_id", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_table("audit_aggregate_sequences")
    op.drop_index(
        "ix_idempotency_records_workspace_id",
        table_name="idempotency_records",
    )
    op.drop_index(
        "ix_idempotency_records_tenant_id",
        table_name="idempotency_records",
    )
    op.drop_table("idempotency_records")
    op.drop_table("membership_roles")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_index("ix_roles_tenant_id", table_name="roles")
    op.drop_table("roles")
    op.drop_index("ix_memberships_user_id", table_name="memberships")
    op.drop_index("ix_memberships_workspace_id", table_name="memberships")
    op.drop_index("ix_memberships_tenant_id", table_name="memberships")
    op.drop_table("memberships")
    op.drop_table("users")
    op.drop_index("ix_workspaces_tenant_id", table_name="workspaces")
    op.drop_table("workspaces")
    op.drop_table("tenants")
