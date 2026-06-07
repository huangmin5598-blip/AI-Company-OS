"""P0 idempotency, append-only Audit Event, and Audit Packet models."""

from __future__ import annotations

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from app.models.foundation_base import FoundationBase


class IdempotencyRecord(FoundationBase):
    __tablename__ = "idempotency_records"

    idempotency_record_id = Column(String(64), primary_key=True)
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
    actor_id = Column(String(64), nullable=False)
    command = Column(String(160), nullable=False)
    target_type = Column(String(80), nullable=False)
    target_id = Column(String(160), nullable=False)
    idempotency_key = Column(String(240), nullable=False)
    request_payload_hash = Column(String(80), nullable=False)
    status = Column(String(32), nullable=False, default="in_progress")
    response_ref = Column(String(500), nullable=True)
    response_hash = Column(String(80), nullable=True)
    correlation_id = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "scope_key",
            "actor_id",
            "command",
            "target_type",
            "target_id",
            "idempotency_key",
            name="uq_idempotency_command_scope",
        ),
    )


class AuditAggregateSequence(FoundationBase):
    __tablename__ = "audit_aggregate_sequences"

    sequence_id = Column(String(64), primary_key=True)
    tenant_id = Column(
        String(64),
        ForeignKey("tenants.tenant_id", ondelete="RESTRICT"),
        nullable=False,
    )
    workspace_id = Column(
        String(64),
        ForeignKey("workspaces.workspace_id", ondelete="RESTRICT"),
        nullable=True,
    )
    scope_key = Column(String(160), nullable=False)
    aggregate_type = Column(String(80), nullable=False)
    aggregate_id = Column(String(160), nullable=False)
    last_sequence = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint(
            "scope_key",
            "aggregate_type",
            "aggregate_id",
            name="uq_audit_aggregate_sequence",
        ),
    )


class AuditEvent(FoundationBase):
    __tablename__ = "audit_events"

    audit_event_id = Column(String(64), primary_key=True)
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
    aggregate_type = Column(String(80), nullable=False)
    aggregate_id = Column(String(160), nullable=False)
    aggregate_sequence = Column(Integer, nullable=False)
    event_type = Column(String(160), nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    occurred_at_source = Column(String(64), nullable=False)
    actor_type = Column(String(64), nullable=False)
    actor_id = Column(String(64), nullable=False)
    mode = Column(String(32), nullable=False)
    source_type = Column(String(80), nullable=False)
    source_id = Column(String(240), nullable=True)
    correlation_id = Column(String(64), nullable=False)
    causation_id = Column(String(64), nullable=True)
    summary = Column(Text, nullable=False)
    payload_ref = Column(String(500), nullable=True)
    payload_hash = Column(String(80), nullable=False)
    provenance_json = Column(Text, nullable=False, default="{}")
    work_order_id = Column(String(160), nullable=True, index=True)
    attempt_id = Column(String(160), nullable=True, index=True)
    approval_id = Column(String(160), nullable=True)
    review_id = Column(String(160), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "scope_key",
            "aggregate_type",
            "aggregate_id",
            "aggregate_sequence",
            name="uq_audit_event_aggregate_sequence",
        ),
    )


class AuditPacket(FoundationBase):
    __tablename__ = "audit_packets"

    audit_packet_id = Column(String(64), primary_key=True)
    audit_event_id = Column(
        String(64),
        ForeignKey("audit_events.audit_event_id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    actor_id = Column(String(64), nullable=False)
    actor_type = Column(String(64), nullable=False)
    mode = Column(String(32), nullable=False)
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
    work_order_id = Column(String(160), nullable=True)
    attempt_id = Column(String(160), nullable=True)
    action_type = Column(String(160), nullable=False)
    invocation_authenticity_ref = Column(String(500), nullable=True)
    result_ref = Column(String(500), nullable=True)
    evidence_refs_json = Column(Text, nullable=False, default="[]")
    produced_at = Column(DateTime(timezone=True), nullable=False)
    payload_hash = Column(String(80), nullable=False)
    previous_event_ref = Column(String(64), nullable=True)
    reviewer_ref = Column(String(160), nullable=True)
    idempotency_ref = Column(
        String(64),
        ForeignKey(
            "idempotency_records.idempotency_record_id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )
