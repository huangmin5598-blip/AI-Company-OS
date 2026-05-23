"""Routers for OrgMemory entries — CRUD + source chain."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.orm import joinedload
from typing import Optional
import json

from app.database import get_async_session
from app.models.org_memory import OrgMemory
from app.schemas.org_memory import OrgMemoryCreate, OrgMemoryResponse

router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


@router.get("/entries", response_model=list[OrgMemoryResponse])
async def list_memory_entries(
    business_line: Optional[str] = None,
    memory_type: Optional[str] = None,
    status: Optional[str] = "active",
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
):
    """List org_memory entries with optional filters."""
    stmt = select(OrgMemory)
    if business_line:
        stmt = stmt.where(OrgMemory.business_line == business_line)
    if memory_type:
        stmt = stmt.where(OrgMemory.memory_type == memory_type)
    if status:
        stmt = stmt.where(OrgMemory.status == status)
    stmt = stmt.order_by(OrgMemory.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    entries = result.scalars().all()
    return entries


@router.get("/entries/{entry_id}", response_model=OrgMemoryResponse)
async def get_memory_entry(
    entry_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """Get a single memory entry with full source chain info."""
    stmt = select(OrgMemory).where(OrgMemory.id == entry_id)
    result = await session.execute(stmt)
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    return entry


@router.post("/entries", response_model=OrgMemoryResponse, status_code=201)
async def create_memory_entry(
    body: OrgMemoryCreate,
    session: AsyncSession = Depends(get_async_session),
):
    """Manually create a memory entry (admin use)."""
    entry = OrgMemory(**body.model_dump())
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry
