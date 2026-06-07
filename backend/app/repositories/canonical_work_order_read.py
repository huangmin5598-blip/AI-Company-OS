"""Scoped canonical WorkOrder reads."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.canonical_work_order import CanonicalWorkOrder
from app.repositories.scoped import ScopedReadRepository


class CanonicalWorkOrderReadRepository(
    ScopedReadRepository[CanonicalWorkOrder]
):
    def __init__(self, session: Session):
        super().__init__(
            session,
            CanonicalWorkOrder,
            id_attribute="work_order_id",
            read_permission="work_order.read",
        )


__all__ = ["CanonicalWorkOrderReadRepository"]
