"""Governed promotion of Native Agent output into an OS candidate record."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy.orm import Session

from app.foundation.canonical_json import canonical_json_bytes, payload_hash
from app.foundation.clock import utc_now
from app.foundation.context import RequestContext
from app.foundation.identity import new_id
from app.models.foundation_execution import PromotionRecord
from app.services.audit_service import append_audit_event
from app.services.idempotency_service import (
    begin_idempotent_command,
    complete_idempotent_command,
)


SENSITIVE_SOURCE_DOMAINS = frozenset({"customer", "support", "conversation"})
PROMOTION_TARGET_TYPES = frozenset(
    {
        "intake",
        "goal",
        "requirement_brief",
        "prd",
        "work_order",
        "founder_decision",
        "company_context_candidate",
        "learning_event_candidate",
        "asset_candidate",
        "opportunity",
    }
)


@dataclass(frozen=True)
class PromotionResult:
    record: PromotionRecord
    replay: bool


def promote_native_output(
    session: Session,
    request: RequestContext,
    *,
    intake_id: str,
    source_conversation_ref: str,
    source_provider: str,
    source_domain: str,
    promotion_rationale: str,
    target_object_type: str,
    accepted_context_refs: Iterable[str],
    rejected_context_refs: Iterable[str],
    review_required: bool,
    target_work_order_id: str | None = None,
    target_project_id: str | None = None,
) -> PromotionResult:
    request.scope.require("promotion.create")
    if request.mode != "promotion":
        raise ValueError("promotion_mode_required")
    if target_object_type not in PROMOTION_TARGET_TYPES:
        raise ValueError("unsupported_promotion_target")
    if (
        source_domain in SENSITIVE_SOURCE_DOMAINS
        and "customer_data.promote" not in request.scope.principal.permission_names
        and "*" not in request.scope.principal.permission_names
    ):
        request.scope.require("customer_data.promote")

    accepted = list(accepted_context_refs)
    rejected = list(rejected_context_refs)
    command_payload = {
        "intake_id": intake_id,
        "source_conversation_ref": source_conversation_ref,
        "source_provider": source_provider,
        "source_domain": source_domain,
        "promotion_rationale": promotion_rationale,
        "target_object_type": target_object_type,
        "target_work_order_id": target_work_order_id,
        "target_project_id": target_project_id,
        "accepted_context_refs": accepted,
        "rejected_context_refs": rejected,
        "review_required": review_required,
    }
    promotion_key = payload_hash(
        {
            "scope_key": request.scope.scope_key,
            "source_conversation_ref": source_conversation_ref,
            "target_object_type": target_object_type,
            "target_work_order_id": target_work_order_id,
            "target_project_id": target_project_id,
        }
    )
    idempotency = begin_idempotent_command(
        session,
        request,
        command="native_output.promote",
        target_type=target_object_type,
        target_id=promotion_key,
        request_payload=command_payload,
    )
    if not idempotency.created:
        record = session.query(PromotionRecord).filter_by(
            idempotency_ref=idempotency.record.idempotency_record_id
        ).one()
        return PromotionResult(record=record, replay=True)

    promotion_id = new_id("promo")
    event = append_audit_event(
        session,
        request,
        aggregate_type="promotion",
        aggregate_id=promotion_id,
        event_type="native_output.promoted",
        source_type=request.origin.value,
        source_id=source_conversation_ref,
        summary="Native Agent output promoted to governed candidate",
        payload=command_payload,
        provenance={
            "original_mode": "native",
            "source_provider": source_provider,
            "source_domain": source_domain,
            "target_is_candidate": True,
        },
        work_order_id=target_work_order_id,
    )
    record = PromotionRecord(
        promotion_id=promotion_id,
        promotion_key=promotion_key,
        tenant_id=request.scope.tenant_id,
        workspace_id=request.scope.workspace_id,
        scope_key=request.scope.scope_key,
        intake_id=intake_id,
        source_conversation_ref=source_conversation_ref,
        source_provider=source_provider,
        source_domain=source_domain,
        original_mode="native",
        promoted_mode="promotion",
        promoted_by=request.scope.principal_id,
        promoted_at=utc_now(),
        promotion_rationale=promotion_rationale,
        target_object_type=target_object_type,
        target_work_order_id=target_work_order_id,
        target_project_id=target_project_id,
        accepted_context_refs_json=canonical_json_bytes(accepted).decode("utf-8"),
        rejected_context_refs_json=canonical_json_bytes(rejected).decode("utf-8"),
        review_required=review_required,
        audit_event_ref=event.audit_event_id,
        idempotency_ref=idempotency.record.idempotency_record_id,
    )
    session.add(record)
    session.flush()
    complete_idempotent_command(
        idempotency.record,
        response_ref=f"promotion://{promotion_id}",
        response_payload={"promotion_id": promotion_id},
    )
    return PromotionResult(record=record, replay=False)
