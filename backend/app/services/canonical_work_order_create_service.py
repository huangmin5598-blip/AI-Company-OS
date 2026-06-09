"""Named, idempotent creation of a canonical draft WorkOrder."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.foundation.context import RequestContext
from app.models.foundation_audit import AuditEvent, AuditPacket
from app.repositories.canonical_work_order_command import (
    CanonicalCommandRejected,
    CanonicalWorkOrderCommandRepository,
)
from app.services.audit_service import append_audit_event, create_audit_packet
from app.services.idempotency_service import (
    begin_idempotent_command,
    complete_idempotent_command,
)


@dataclass(frozen=True)
class CreateDraftReceipt:
    work_order_id: str
    work_order_state: str
    work_order_row_version: int
    audit_event_id: str
    audit_packet_id: str
    replayed: bool = False


def _deterministic_work_order_id(request: RequestContext) -> str:
    if not request.idempotency_key:
        raise ValueError("idempotency_key_required")
    material = "\0".join(
        (
            request.scope.scope_key,
            request.scope.principal_id,
            request.idempotency_key,
            "work_order.create_draft",
        )
    ).encode("utf-8")
    return "wo_" + hashlib.sha256(material).hexdigest()[:32]


def create_canonical_draft(
    session: Session,
    request: RequestContext,
    *,
    skill_id: str,
    task_type: str,
    input_context: str,
    expected_output: str,
) -> CreateDraftReceipt:
    request.scope.require("work_order.create")
    command = "work_order.create_draft"
    work_order_id = _deterministic_work_order_id(request)
    payload = {
        "work_order_id": work_order_id,
        "skill_id": skill_id,
        "task_type": task_type,
        "input_context": input_context,
        "expected_output": expected_output,
    }
    with session.begin_nested():
        idempotency = begin_idempotent_command(
            session,
            request,
            command=command,
            target_type="work_order",
            target_id=work_order_id,
            request_payload=payload,
        )
        if idempotency.replay:
            packet = session.execute(
                select(AuditPacket).where(
                    AuditPacket.idempotency_ref
                    == idempotency.record.idempotency_record_id,
                    AuditPacket.work_order_id == work_order_id,
                )
            ).scalar_one_or_none()
            if packet is None:
                raise CanonicalCommandRejected(
                    "idempotency_replay_evidence_missing"
                )
            event = session.get(AuditEvent, packet.audit_event_id)
            if event is None:
                raise CanonicalCommandRejected(
                    "idempotency_replay_evidence_missing"
                )
            return CreateDraftReceipt(
                work_order_id=work_order_id,
                work_order_state="draft",
                work_order_row_version=1,
                audit_event_id=event.audit_event_id,
                audit_packet_id=packet.audit_packet_id,
                replayed=True,
            )

        work_order = CanonicalWorkOrderCommandRepository(session).create_draft(
            request.scope,
            work_order_id=work_order_id,
            skill_id=skill_id,
            task_type=task_type,
            input_context=input_context,
            expected_output=expected_output,
        )
        event = append_audit_event(
            session,
            request,
            aggregate_type="work_order",
            aggregate_id=work_order_id,
            event_type=command,
            source_type=request.origin.value,
            summary=command,
            payload=payload,
            provenance={
                "named_command": True,
                "pilot_authority": "pilot_non_authoritative",
            },
            work_order_id=work_order_id,
        )
        packet = create_audit_packet(
            session,
            request,
            event=event,
            action_type=command,
            evidence_refs=(),
            idempotency_record=idempotency.record,
            work_order_id=work_order_id,
        )
        response = {
            "work_order_id": work_order_id,
            "work_order_state": work_order.canonical_state,
            "work_order_row_version": work_order.row_version,
            "audit_packet_id": packet.audit_packet_id,
        }
        complete_idempotent_command(
            idempotency.record,
            response_ref=json.dumps(
                response,
                sort_keys=True,
                separators=(",", ":"),
            ),
            response_payload=response,
        )
        return CreateDraftReceipt(
            work_order_id=work_order_id,
            work_order_state="draft",
            work_order_row_version=1,
            audit_event_id=event.audit_event_id,
            audit_packet_id=packet.audit_packet_id,
        )


__all__ = ["CreateDraftReceipt", "create_canonical_draft"]
