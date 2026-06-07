"""Tenant/Workspace-scoped repository base."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy.orm import Session

from app.foundation.context import ScopeContext


ModelT = TypeVar("ModelT")


class RepositoryScopeError(ValueError):
    pass


class ScopedRepository(Generic[ModelT]):
    def __init__(
        self,
        session: Session,
        model: type[ModelT],
        *,
        id_attribute: str,
        read_permission: str,
        write_permission: str,
        workspace_scoped: bool = True,
    ):
        self._session = session
        self._model = model
        self._id_attribute = id_attribute
        self._read_permission = read_permission
        self._write_permission = write_permission
        self._workspace_scoped = workspace_scoped
        for required_attribute in ("tenant_id", id_attribute):
            if not hasattr(model, required_attribute):
                raise TypeError(f"Scoped model lacks {required_attribute}")
        if workspace_scoped and not hasattr(model, "workspace_id"):
            raise TypeError("Workspace-scoped model lacks workspace_id")

    def _query(self, scope: ScopeContext):
        if self._workspace_scoped and scope.workspace_id is None:
            raise RepositoryScopeError("workspace_scope_required")
        query = self._session.query(self._model).filter(
            getattr(self._model, "tenant_id") == scope.tenant_id
        )
        if self._workspace_scoped:
            query = query.filter(
                getattr(self._model, "workspace_id") == scope.workspace_id
            )
        return query

    def get_by_id(self, scope: ScopeContext, object_id: str) -> ModelT | None:
        scope.require(self._read_permission)
        return self._query(scope).filter(
            getattr(self._model, self._id_attribute) == object_id
        ).first()

    def list(self, scope: ScopeContext, *, limit: int = 100, offset: int = 0) -> list[ModelT]:
        scope.require(self._read_permission)
        if limit < 1 or limit > 500 or offset < 0:
            raise ValueError("invalid_pagination")
        return self._query(scope).offset(offset).limit(limit).all()

    def count(self, scope: ScopeContext) -> int:
        scope.require(self._read_permission)
        return self._query(scope).count()

    def add(self, scope: ScopeContext, entity: ModelT) -> ModelT:
        scope.require(self._write_permission)
        if getattr(entity, "tenant_id") != scope.tenant_id:
            raise RepositoryScopeError("entity_tenant_mismatch")
        if (
            self._workspace_scoped
            and getattr(entity, "workspace_id") != scope.workspace_id
        ):
            raise RepositoryScopeError("entity_workspace_mismatch")
        self._session.add(entity)
        return entity
