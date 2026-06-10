"""Scoped persistence for VS-002 pilot artifacts and asset candidates."""

from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.foundation.context import ScopeContext
from app.models.pilot_asset import PilotArtifact, PilotAsset, PilotAssetArtifact
from app.repositories.scoped import ScopedCommandRepository


class PilotAssetConflict(RuntimeError):
    pass


class PilotArtifactRepository(ScopedCommandRepository[PilotArtifact]):
    def __init__(self, session: Session):
        super().__init__(
            session,
            PilotArtifact,
            id_attribute="artifact_id",
            read_permission="artifact.read",
        )

    def capture_artifact(
        self,
        scope: ScopeContext,
        artifact: PilotArtifact,
    ) -> PilotArtifact:
        scope.require("work_order.execute")
        existing = self._session.execute(
            select(PilotArtifact).where(
                PilotArtifact.scope_key == scope.scope_key,
                PilotArtifact.attempt_id == artifact.attempt_id,
                PilotArtifact.content_hash == artifact.content_hash,
            )
        ).scalar_one_or_none()
        if existing is not None:
            if (
                existing.work_order_id != artifact.work_order_id
                or existing.content_text != artifact.content_text
            ):
                raise PilotAssetConflict("artifact_capture_conflict")
            return existing
        conflicting = self._session.execute(
            select(PilotArtifact).where(
                PilotArtifact.scope_key == scope.scope_key,
                PilotArtifact.attempt_id == artifact.attempt_id,
            )
        ).scalar_one_or_none()
        if conflicting is not None:
            raise PilotAssetConflict("attempt_artifact_hash_conflict")
        self._session.add(artifact)
        self._session.flush()
        return artifact


class PilotAssetRepository(ScopedCommandRepository[PilotAsset]):
    def __init__(self, session: Session):
        super().__init__(
            session,
            PilotAsset,
            id_attribute="asset_id",
            read_permission="asset.read",
        )

    def create_candidate(
        self,
        scope: ScopeContext,
        asset: PilotAsset,
        links: list[PilotAssetArtifact],
    ) -> PilotAsset:
        scope.require("asset.promote")
        existing = self._session.execute(
            select(PilotAsset).where(
                PilotAsset.scope_key == scope.scope_key,
                PilotAsset.source_review_id == asset.source_review_id,
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing
        self._session.add(asset)
        self._session.flush()
        self._session.add_all(links)
        self._session.flush()
        return asset

    def approve_candidate(
        self,
        scope: ScopeContext,
        *,
        asset_id: str,
        approval_id: str,
        expected_row_version: int,
        approved_by: str,
        approved_at,
    ) -> PilotAsset:
        scope.require("asset.promote")
        statement = (
            update(PilotAsset)
            .where(
                PilotAsset.asset_id == asset_id,
                PilotAsset.tenant_id == scope.tenant_id,
                PilotAsset.workspace_id == scope.workspace_id,
                PilotAsset.status == "candidate",
                PilotAsset.row_version == expected_row_version,
            )
            .values(
                status="approved",
                approval_id=approval_id,
                approved_by=approved_by,
                approved_at=approved_at,
                row_version=expected_row_version + 1,
            )
        )
        if self._session.execute(statement).rowcount != 1:
            raise PilotAssetConflict("asset_approval_conflict")
        self._session.flush()
        asset = self.get_by_id(scope, asset_id)
        if asset is None:
            raise PilotAssetConflict("asset_not_found")
        return asset


__all__ = [
    "PilotArtifactRepository",
    "PilotAssetConflict",
    "PilotAssetRepository",
]
