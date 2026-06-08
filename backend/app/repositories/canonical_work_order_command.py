"""Scoped compare-and-set persistence for canonical WorkOrder commands."""

from __future__ import annotations

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.foundation.context import ScopeContext
from app.foundation.work_order_state import CANONICAL_STATES, is_legal_transition
from app.models.canonical_work_order import CanonicalWorkOrder
from app.repositories.scoped import ScopedCommandRepository


class CanonicalCommandRejected(RuntimeError):
    pass


class CanonicalWorkOrderCommandRepository(
    ScopedCommandRepository[CanonicalWorkOrder]
):
    def __init__(self, session: Session):
        super().__init__(
            session,
            CanonicalWorkOrder,
            id_attribute="work_order_id",
            read_permission="work_order.read",
        )

    def require_canonical(
        self,
        scope: ScopeContext,
        work_order_id: str,
    ) -> CanonicalWorkOrder:
        work_order = self.get_by_id(scope, work_order_id)
        if work_order is None:
            raise CanonicalCommandRejected("canonical_work_order_not_found")
        if (
            work_order.canonical_state not in CANONICAL_STATES
            or work_order.row_version is None
            or work_order.row_version < 1
        ):
            raise CanonicalCommandRejected("canonical_work_order_unresolved")
        return work_order

    def _compare_and_set_state(
        self,
        scope: ScopeContext,
        *,
        work_order_id: str,
        from_state: str,
        to_state: str,
        expected_row_version: int,
    ) -> CanonicalWorkOrder:
        if not is_legal_transition(from_state, to_state):
            raise CanonicalCommandRejected("illegal_work_order_transition")
        values: dict[str, object] = {
            "canonical_state": to_state,
            "row_version": expected_row_version + 1,
        }
        statement = (
            update(CanonicalWorkOrder)
            .where(
                CanonicalWorkOrder.work_order_id == work_order_id,
                CanonicalWorkOrder.tenant_id == scope.tenant_id,
                CanonicalWorkOrder.workspace_id == scope.workspace_id,
                CanonicalWorkOrder.canonical_state == from_state,
                CanonicalWorkOrder.row_version == expected_row_version,
            )
            .values(**values)
        )
        if self._session.execute(statement).rowcount != 1:
            raise CanonicalCommandRejected("work_order_state_conflict")
        self._session.flush()
        work_order = self.get_by_id(scope, work_order_id)
        if work_order is None:
            raise CanonicalCommandRejected("canonical_work_order_not_found")
        return work_order

    def request_approval(
        self,
        scope: ScopeContext,
        *,
        work_order_id: str,
        expected_row_version: int,
    ) -> CanonicalWorkOrder:
        scope.require("work_order.execute")
        return self._compare_and_set_state(
            scope,
            work_order_id=work_order_id,
            from_state="draft",
            to_state="waiting_approval",
            expected_row_version=expected_row_version,
        )

    def apply_approval_decision(
        self,
        scope: ScopeContext,
        *,
        work_order_id: str,
        decision: str,
        expected_row_version: int,
    ) -> CanonicalWorkOrder:
        scope.require("approval.decide")
        target = {"approved": "queued", "rejected": "cancelled"}.get(decision)
        if target is None:
            raise CanonicalCommandRejected("unsupported_approval_decision")
        return self._compare_and_set_state(
            scope,
            work_order_id=work_order_id,
            from_state="waiting_approval",
            to_state=target,
            expected_row_version=expected_row_version,
        )

    def mark_running_after_claim(
        self,
        scope: ScopeContext,
        *,
        work_order_id: str,
        expected_row_version: int,
    ) -> CanonicalWorkOrder:
        scope.require("work_order.execute")
        return self._compare_and_set_state(
            scope,
            work_order_id=work_order_id,
            from_state="queued",
            to_state="running",
            expected_row_version=expected_row_version,
        )

    def mark_waiting_review_after_result(
        self,
        scope: ScopeContext,
        *,
        work_order_id: str,
        expected_row_version: int,
    ) -> CanonicalWorkOrder:
        scope.require("work_order.execute")
        return self._compare_and_set_state(
            scope,
            work_order_id=work_order_id,
            from_state="running",
            to_state="waiting_review",
            expected_row_version=expected_row_version,
        )

    def apply_review_outcome(
        self,
        scope: ScopeContext,
        *,
        work_order_id: str,
        decision: str,
        expected_row_version: int,
    ) -> CanonicalWorkOrder:
        scope.require("review.decide")
        target = {
            "passed": "done",
            "revision_required": "revision_required",
            "failed": "failed",
            "cancelled": "cancelled",
        }.get(decision)
        if target is None:
            raise CanonicalCommandRejected("unsupported_review_decision")
        return self._compare_and_set_state(
            scope,
            work_order_id=work_order_id,
            from_state="waiting_review",
            to_state=target,
            expected_row_version=expected_row_version,
        )


__all__ = [
    "CanonicalCommandRejected",
    "CanonicalWorkOrderCommandRepository",
]
