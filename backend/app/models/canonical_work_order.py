"""Canonical read mapping for the existing ``work_orders`` table."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, MetaData, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class CanonicalReadBase(DeclarativeBase):
    metadata = MetaData()


class CanonicalWorkOrder(CanonicalReadBase):
    __tablename__ = "work_orders"

    work_order_id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    workspace_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    skill_id: Mapped[str] = mapped_column(String, nullable=False)
    task_type: Mapped[str] = mapped_column(String, nullable=False, default="")
    input_context: Mapped[str] = mapped_column(Text, nullable=False, default="")
    expected_output: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    canonical_state: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    row_version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    terminal_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    result_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    error: Mapped[str] = mapped_column(Text, nullable=False, default="")
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    visibility: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    parallel_attempts_allowed: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
    )
    max_attempts: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


__all__ = ["CanonicalReadBase", "CanonicalWorkOrder"]
