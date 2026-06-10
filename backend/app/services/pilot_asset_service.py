"""OS-governed pilot Artifact capture and Asset candidate approval."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.foundation.canonical_json import canonical_json_bytes, payload_hash
from app.foundation.clock import utc_now
from app.foundation.context import (
    AuthenticationMethod,
    PrincipalType,
    RequestContext,
)
from app.foundation.identity import new_id
from app.models.foundation_audit import AuditEvent, AuditPacket
from app.models.foundation_execution import WorkApproval, WorkAttempt, WorkReview
from app.models.pilot_asset import PilotArtifact, PilotAsset, PilotAssetArtifact
from app.repositories.pilot_asset import (
    PilotArtifactRepository,
    PilotAssetRepository,
)
from app.services.audit_service import append_audit_event, create_audit_packet
from app.services.execution_persistence_service import (
    create_approval_request,
    decide_approval,
)
from app.services.idempotency_service import (
    begin_idempotent_command,
    complete_idempotent_command,
)


PILOT_AUTHORITY = "pilot_non_authoritative"
PILOT_VISIBILITY = "restricted"
SOURCE_PATH = "os_governed_work_review"
MAX_ARTIFACT_BYTES = 256 * 1024
MARKDOWN_MEDIA_TYPE = "text/markdown; charset=utf-8"


@dataclass(frozen=True)
class ArtifactCaptureReceipt:
    artifact_id: str
    content_hash: str
    audit_event_id: str
    audit_packet_id: str
    replayed: bool = False


@dataclass(frozen=True)
class AssetCommandReceipt:
    asset_id: str
    status: str
    row_version: int
    approval_id: str
    audit_event_id: str
    audit_packet_id: str
    replayed: bool = False


def _sha256(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def artifact_set_hash(
    artifacts: Iterable[tuple[str, str]],
) -> str:
    return payload_hash(
        [
            {"artifact_id": artifact_id, "content_hash": content_hash}
            for artifact_id, content_hash in sorted(artifacts)
        ]
    )


def _parse_response(response_ref: str | None) -> dict[str, object]:
    try:
        value = json.loads(response_ref or "")
    except json.JSONDecodeError as exc:
        raise RuntimeError("asset_idempotency_response_missing") from exc
    if not isinstance(value, dict):
        raise RuntimeError("asset_idempotency_response_missing")
    return value


def capture_attempt_artifact(
    session: Session,
    request: RequestContext,
    *,
    work_order_id: str,
    attempt_id: str,
    source_ref: str,
    content: bytes,
    expected_content_hash: str,
) -> ArtifactCaptureReceipt:
    request.scope.require("work_order.execute")
    if len(content) > MAX_ARTIFACT_BYTES:
        raise ValueError("artifact_size_limit_exceeded")
    try:
        content_text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("artifact_utf8_required") from exc
    actual_hash = _sha256(content)
    if actual_hash != expected_content_hash:
        raise ValueError("artifact_content_hash_mismatch")
    attempt = session.execute(
        select(WorkAttempt).where(
            WorkAttempt.attempt_id == attempt_id,
            WorkAttempt.work_order_id == work_order_id,
            WorkAttempt.scope_key == request.scope.scope_key,
            WorkAttempt.state == "running",
        )
    ).scalar_one_or_none()
    if attempt is None:
        raise ValueError("artifact_capture_requires_running_attempt")

    command = "artifact.captured"
    command_payload = {
        "work_order_id": work_order_id,
        "attempt_id": attempt_id,
        "content_hash": actual_hash,
        "media_type": MARKDOWN_MEDIA_TYPE,
        "size_bytes": len(content),
    }
    idempotency = begin_idempotent_command(
        session,
        request,
        command=command,
        target_type="attempt",
        target_id=attempt_id,
        request_payload=command_payload,
    )
    if idempotency.replay:
        response = _parse_response(idempotency.record.response_ref)
        return ArtifactCaptureReceipt(
            artifact_id=str(response["artifact_id"]),
            content_hash=str(response["content_hash"]),
            audit_event_id=str(response["audit_event_id"]),
            audit_packet_id=str(response["audit_packet_id"]),
            replayed=True,
        )

    artifact_id = new_id("art")
    artifact = PilotArtifact(
        artifact_id=artifact_id,
        tenant_id=request.scope.tenant_id,
        workspace_id=request.scope.workspace_id,
        scope_key=request.scope.scope_key,
        work_order_id=work_order_id,
        attempt_id=attempt_id,
        source_ref=source_ref,
        storage_ref=f"pilot-db://pilot_artifacts/{artifact_id}/content",
        content_hash=actual_hash,
        media_type=MARKDOWN_MEDIA_TYPE,
        size_bytes=len(content),
        sensitivity="internal",
        validation_status="verified",
        authority=PILOT_AUTHORITY,
        visibility=PILOT_VISIBILITY,
        source_path=SOURCE_PATH,
        source_authority=PILOT_AUTHORITY,
        provenance_json=canonical_json_bytes(
            {
                "attempt_id": attempt_id,
                "work_order_id": work_order_id,
                "exact_byte_hash": actual_hash,
                "source_ref": source_ref,
            }
        ).decode("utf-8"),
        content_text=content_text,
        created_by=request.scope.principal_id,
        created_at=utc_now(),
    )
    artifact = PilotArtifactRepository(session).capture_artifact(
        request.scope,
        artifact,
    )
    event = append_audit_event(
        session,
        request,
        aggregate_type="artifact",
        aggregate_id=artifact.artifact_id,
        event_type=command,
        source_type=request.origin.value,
        summary="Pilot attempt result captured as immutable Artifact",
        payload=command_payload,
        provenance={
            "authority": PILOT_AUTHORITY,
            "visibility": PILOT_VISIBILITY,
            "source_path": SOURCE_PATH,
        },
        work_order_id=work_order_id,
        attempt_id=attempt_id,
    )
    packet = create_audit_packet(
        session,
        request,
        event=event,
        action_type=command,
        evidence_refs=[f"artifact://{artifact.artifact_id}", actual_hash],
        idempotency_record=idempotency.record,
        work_order_id=work_order_id,
        attempt_id=attempt_id,
        result_ref=f"artifact://{artifact.artifact_id}",
    )
    response = {
        "artifact_id": artifact.artifact_id,
        "content_hash": actual_hash,
        "audit_event_id": event.audit_event_id,
        "audit_packet_id": packet.audit_packet_id,
    }
    complete_idempotent_command(
        idempotency.record,
        response_ref=json.dumps(response, sort_keys=True, separators=(",", ":")),
        response_payload=response,
    )
    return ArtifactCaptureReceipt(**response)


def create_asset_candidate(
    session: Session,
    request: RequestContext,
    *,
    review_id: str,
    title: str,
) -> AssetCommandReceipt:
    request.scope.require("asset.promote")
    review = session.execute(
        select(WorkReview).where(
            WorkReview.review_id == review_id,
            WorkReview.scope_key == request.scope.scope_key,
            WorkReview.state == "passed",
        )
    ).scalar_one_or_none()
    if review is None:
        raise ValueError("asset_candidate_requires_passed_review")
    artifact_ids = json.loads(review.artifact_ids_json)
    criteria = json.loads(review.criteria_snapshot_json)
    if (
        not isinstance(artifact_ids, list)
        or not artifact_ids
        or not all(isinstance(value, str) for value in artifact_ids)
        or not criteria.get("artifact_set_hash")
    ):
        raise ValueError("review_artifact_lineage_missing")
    artifacts = session.execute(
        select(PilotArtifact).where(
            PilotArtifact.scope_key == request.scope.scope_key,
            PilotArtifact.artifact_id.in_(artifact_ids),
        )
    ).scalars().all()
    if len(artifacts) != len(artifact_ids):
        raise ValueError("review_artifact_scope_mismatch")
    calculated_set_hash = artifact_set_hash(
        (artifact.artifact_id, artifact.content_hash)
        for artifact in artifacts
    )
    if calculated_set_hash != criteria["artifact_set_hash"]:
        raise ValueError("review_artifact_set_hash_mismatch")

    command = "asset.candidate_created"
    command_payload = {
        "review_id": review_id,
        "work_order_id": review.work_order_id,
        "artifact_ids": sorted(artifact_ids),
        "artifact_set_hash": calculated_set_hash,
    }
    idempotency = begin_idempotent_command(
        session,
        request,
        command=command,
        target_type="work_review",
        target_id=review_id,
        request_payload=command_payload,
    )
    if idempotency.replay:
        response = _parse_response(idempotency.record.response_ref)
        return AssetCommandReceipt(
            asset_id=str(response["asset_id"]),
            status=str(response["status"]),
            row_version=int(response["row_version"]),
            approval_id=str(response["approval_id"]),
            audit_event_id=str(response["audit_event_id"]),
            audit_packet_id=str(response["audit_packet_id"]),
            replayed=True,
        )

    existing_asset = session.execute(
        select(PilotAsset).where(
            PilotAsset.scope_key == request.scope.scope_key,
            PilotAsset.source_review_id == review_id,
        )
    ).scalar_one_or_none()
    if existing_asset is not None:
        existing_approval = session.execute(
            select(WorkApproval).where(
                WorkApproval.scope_key == request.scope.scope_key,
                WorkApproval.target_type == "asset_candidate",
                WorkApproval.target_id == existing_asset.asset_id,
                WorkApproval.action == "promote_to_asset",
            )
        ).scalar_one_or_none()
        existing_event = session.execute(
            select(AuditEvent).where(
                AuditEvent.scope_key == request.scope.scope_key,
                AuditEvent.aggregate_type == "asset",
                AuditEvent.aggregate_id == existing_asset.asset_id,
                AuditEvent.event_type == command,
            )
        ).scalar_one_or_none()
        existing_packet = (
            None
            if existing_event is None
            else session.execute(
                select(AuditPacket).where(
                    AuditPacket.audit_event_id == existing_event.audit_event_id
                )
            ).scalar_one_or_none()
        )
        if (
            existing_approval is None
            or existing_event is None
            or existing_packet is None
        ):
            raise RuntimeError("asset_candidate_lineage_incomplete")
        response = {
            "asset_id": existing_asset.asset_id,
            "status": existing_asset.status,
            "row_version": existing_asset.row_version,
            "approval_id": existing_approval.approval_id,
            "audit_event_id": existing_event.audit_event_id,
            "audit_packet_id": existing_packet.audit_packet_id,
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
        return AssetCommandReceipt(**response, replayed=True)

    primary = sorted(artifacts, key=lambda item: item.artifact_id)[0]
    asset_id = new_id("ast")
    now = utc_now()
    asset = PilotAsset(
        asset_id=asset_id,
        tenant_id=request.scope.tenant_id,
        workspace_id=request.scope.workspace_id,
        scope_key=request.scope.scope_key,
        title=title[:240],
        asset_type="markdown_document",
        source_work_order_id=review.work_order_id,
        source_review_id=review.review_id,
        version=1,
        status="candidate",
        content_ref=f"artifact://{primary.artifact_id}",
        public_safe_ref=None,
        sensitivity="internal",
        visibility=PILOT_VISIBILITY,
        authority=PILOT_AUTHORITY,
        source_path=SOURCE_PATH,
        source_authority=PILOT_AUTHORITY,
        owner_id=request.scope.principal_id,
        approval_id=None,
        row_version=1,
        created_by=request.scope.principal_id,
        created_at=now,
        approved_by=None,
        approved_at=None,
    )
    links = [
        PilotAssetArtifact(
            asset_id=asset_id,
            artifact_id=artifact.artifact_id,
            tenant_id=request.scope.tenant_id,
            workspace_id=request.scope.workspace_id,
            scope_key=request.scope.scope_key,
            content_hash=artifact.content_hash,
            created_at=now,
        )
        for artifact in artifacts
    ]
    asset = PilotAssetRepository(session).create_candidate(
        request.scope,
        asset,
        links,
    )
    approval = create_approval_request(
        session,
        request,
        target_type="asset_candidate",
        target_id=asset.asset_id,
        target_version=str(asset.version),
        action="promote_to_asset",
        risk_level="low",
        conditions=[
            "pilot_non_authoritative",
            "restricted_visibility",
            "public_safe_ref_must_remain_null",
        ],
        context_snapshot_ref=f"review://{review.review_id}",
    )
    event = append_audit_event(
        session,
        request,
        aggregate_type="asset",
        aggregate_id=asset.asset_id,
        event_type=command,
        source_type=request.origin.value,
        summary="Passed WorkReview produced a Pilot Asset Candidate",
        payload={**command_payload, "approval_id": approval.approval_id},
        provenance={
            "authority": PILOT_AUTHORITY,
            "visibility": PILOT_VISIBILITY,
            "source_path": SOURCE_PATH,
        },
        work_order_id=review.work_order_id,
        approval_id=approval.approval_id,
        review_id=review.review_id,
    )
    packet = create_audit_packet(
        session,
        request,
        event=event,
        action_type=command,
        evidence_refs=[
            f"review://{review.review_id}",
            *[f"artifact://{artifact_id}" for artifact_id in sorted(artifact_ids)],
            calculated_set_hash,
        ],
        idempotency_record=idempotency.record,
        work_order_id=review.work_order_id,
        reviewer_ref=f"principal://{review.reviewer_id}",
    )
    response = {
        "asset_id": asset.asset_id,
        "status": asset.status,
        "row_version": asset.row_version,
        "approval_id": approval.approval_id,
        "audit_event_id": event.audit_event_id,
        "audit_packet_id": packet.audit_packet_id,
    }
    complete_idempotent_command(
        idempotency.record,
        response_ref=json.dumps(response, sort_keys=True, separators=(",", ":")),
        response_payload=response,
    )
    return AssetCommandReceipt(**response)


def approve_asset_candidate(
    session: Session,
    request: RequestContext,
    *,
    asset_id: str,
    approval_id: str,
    expected_asset_version: int,
    expected_approval_version: int,
) -> AssetCommandReceipt:
    request.scope.require("asset.promote")
    request.scope.require("approval.decide")
    if request.scope.principal_type == "runtime_wrapper":
        raise PermissionError("runtime_wrapper_cannot_approve_asset")
    principal = request.scope.principal
    if (
        principal.principal_id != "local-founder"
        or principal.principal_type is not PrincipalType.HUMAN
        or principal.authentication_method is not AuthenticationMethod.LOCAL_LOOPBACK
        or not principal.local_mode
        or request.mode != "os_governed_pilot"
    ):
        raise PermissionError(
            "pilot_single_actor_asset_approval_exception_not_applicable"
        )
    repository = PilotAssetRepository(session)
    asset = repository.get_by_id(request.scope, asset_id)
    if asset is None:
        raise LookupError("pilot_asset_not_found")
    approval = session.execute(
        select(WorkApproval).where(
            WorkApproval.approval_id == approval_id,
            WorkApproval.scope_key == request.scope.scope_key,
            WorkApproval.target_type == "asset_candidate",
            WorkApproval.target_id == asset_id,
            WorkApproval.target_version == str(asset.version),
            WorkApproval.action == "promote_to_asset",
        )
    ).scalar_one_or_none()
    if approval is None:
        raise ValueError("asset_approval_target_mismatch")
    if (
        approval.risk_level != "low"
        or asset.authority != PILOT_AUTHORITY
        or asset.visibility != PILOT_VISIBILITY
        or asset.public_safe_ref is not None
    ):
        raise PermissionError(
            "pilot_single_actor_asset_approval_exception_not_applicable"
        )
    command = "asset.approved"
    command_payload = {
        "asset_id": asset_id,
        "approval_id": approval_id,
        "expected_asset_version": expected_asset_version,
        "expected_approval_version": expected_approval_version,
    }
    idempotency = begin_idempotent_command(
        session,
        request,
        command=command,
        target_type="asset_candidate",
        target_id=asset_id,
        request_payload=command_payload,
    )
    if idempotency.replay:
        response = _parse_response(idempotency.record.response_ref)
        return AssetCommandReceipt(
            asset_id=str(response["asset_id"]),
            status=str(response["status"]),
            row_version=int(response["row_version"]),
            approval_id=str(response["approval_id"]),
            audit_event_id=str(response["audit_event_id"]),
            audit_packet_id=str(response["audit_packet_id"]),
            replayed=True,
        )
    decided = decide_approval(
        session,
        request,
        approval_id=approval_id,
        decision="approved",
        expected_row_version=expected_approval_version,
        decision_note="Local pilot Asset Candidate approved by Founder",
    )
    approved_at = utc_now()
    asset = repository.approve_candidate(
        request.scope,
        asset_id=asset_id,
        approval_id=approval_id,
        expected_row_version=expected_asset_version,
        approved_by=request.scope.principal_id,
        approved_at=approved_at,
    )
    event = append_audit_event(
        session,
        request,
        aggregate_type="asset",
        aggregate_id=asset.asset_id,
        event_type=command,
        source_type=request.origin.value,
        summary="Founder approved Pilot Asset Candidate",
        payload={**command_payload, "decision": decided.decision},
        provenance={
            "authority": PILOT_AUTHORITY,
            "visibility": PILOT_VISIBILITY,
            "public_safe_ref": None,
        },
        work_order_id=asset.source_work_order_id,
        approval_id=approval_id,
        review_id=asset.source_review_id,
    )
    packet = create_audit_packet(
        session,
        request,
        event=event,
        action_type=command,
        evidence_refs=[
            f"asset://{asset.asset_id}",
            asset.content_ref,
            f"approval://{approval_id}",
        ],
        idempotency_record=idempotency.record,
        work_order_id=asset.source_work_order_id,
        reviewer_ref=f"principal://{request.scope.principal_id}",
    )
    response = {
        "asset_id": asset.asset_id,
        "status": asset.status,
        "row_version": asset.row_version,
        "approval_id": approval_id,
        "audit_event_id": event.audit_event_id,
        "audit_packet_id": packet.audit_packet_id,
    }
    complete_idempotent_command(
        idempotency.record,
        response_ref=json.dumps(response, sort_keys=True, separators=(",", ":")),
        response_payload=response,
    )
    return AssetCommandReceipt(**response)


def asset_envelope(
    session: Session,
    request: RequestContext,
    asset: PilotAsset,
    *,
    include_content: bool,
) -> dict[str, object]:
    request.scope.require("asset.read")
    links = session.execute(
        select(PilotAssetArtifact).where(
            PilotAssetArtifact.scope_key == request.scope.scope_key,
            PilotAssetArtifact.asset_id == asset.asset_id,
        )
    ).scalars().all()
    artifacts = session.execute(
        select(PilotArtifact).where(
            PilotArtifact.scope_key == request.scope.scope_key,
            PilotArtifact.artifact_id.in_(
                [link.artifact_id for link in links]
            ),
        )
    ).scalars().all()
    content = None
    if include_content:
        if len(artifacts) != 1:
            raise ValueError("pilot_asset_primary_artifact_missing")
        primary = artifacts[0]
        if _sha256(primary.content_text.encode("utf-8")) != primary.content_hash:
            raise ValueError("pilot_artifact_integrity_mismatch")
        content = {
            "text": primary.content_text,
            "media_type": primary.media_type,
            "content_hash": primary.content_hash,
            "size_bytes": primary.size_bytes,
        }
    approval = (
        session.get(WorkApproval, asset.approval_id)
        if asset.approval_id is not None
        else session.execute(
            select(WorkApproval)
            .where(
                WorkApproval.scope_key == request.scope.scope_key,
                WorkApproval.target_type == "asset_candidate",
                WorkApproval.target_id == asset.asset_id,
                WorkApproval.action == "promote_to_asset",
            )
            .order_by(WorkApproval.created_at.desc())
        ).scalars().first()
    )
    return {
        "asset": {
            "asset_id": asset.asset_id,
            "title": asset.title,
            "asset_type": asset.asset_type,
            "status": asset.status,
            "version": asset.version,
            "source_work_order_id": asset.source_work_order_id,
            "source_review_id": asset.source_review_id,
            "content_ref": asset.content_ref,
            "public_safe_ref": asset.public_safe_ref,
            "visibility": asset.visibility,
            "authority": asset.authority,
            "source_path": asset.source_path,
            "source_authority": asset.source_authority,
            "row_version": asset.row_version,
            "approval_id": asset.approval_id,
        },
        "artifact_refs": [
            {
                "artifact_id": artifact.artifact_id,
                "content_hash": artifact.content_hash,
                "media_type": artifact.media_type,
                "size_bytes": artifact.size_bytes,
            }
            for artifact in sorted(artifacts, key=lambda item: item.artifact_id)
        ],
        "approval": (
            None
            if approval is None
            else {
                "approval_id": approval.approval_id,
                "decision": approval.decision,
                "row_version": approval.row_version,
                "decided_by": approval.decided_by,
            }
        ),
        "content": content,
        "governance": {
            "authority": PILOT_AUTHORITY,
            "visibility": PILOT_VISIBILITY,
            "public_safe": False,
            "official_asset_center": False,
        },
    }


__all__ = [
    "ArtifactCaptureReceipt",
    "AssetCommandReceipt",
    "PILOT_AUTHORITY",
    "PILOT_VISIBILITY",
    "approve_asset_candidate",
    "artifact_set_hash",
    "asset_envelope",
    "capture_attempt_artifact",
    "create_asset_candidate",
]
