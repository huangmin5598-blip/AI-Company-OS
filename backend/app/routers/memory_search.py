"""Router for OrgMemory search — FTS5 with Chinese-aware LIKE fallback."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, or_
from typing import Optional
import re
import logging

from app.database import get_async_session
from app.models.org_memory import OrgMemory
from app.schemas.org_memory import MemorySearchResult
from app.models.fts_triggers import fts5_available

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


def sanitize_fts5_query(raw: str) -> str:
    """Sanitize FTS5 query: strip special chars, keep alphanumeric + CJK + spaces."""
    if not raw or not raw.strip():
        return ""
    sanitized = re.sub(r'[^\w\u4e00-\u9fff\s]', ' ', raw)
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    if not sanitized:
        return ""
    terms = sanitized.split()
    return ' OR '.join(terms)


async def _like_search(
    session: AsyncSession,
    q: str,
    business_line: str | None = None,
    memory_type: str | None = None,
    limit: int = 20,
) -> list[MemorySearchResult]:
    """LIKE-based search fallback — works with Chinese characters."""
    stmt = select(OrgMemory).where(
        OrgMemory.status == "active",
        or_(
            OrgMemory.title.ilike(f"%{q}%"),
            OrgMemory.summary.ilike(f"%{q}%"),
            OrgMemory.content.ilike(f"%{q}%"),
            OrgMemory.tags.ilike(f"%{q}%"),
        ),
    )
    if business_line:
        stmt = stmt.where(OrgMemory.business_line == business_line)
    if memory_type:
        stmt = stmt.where(OrgMemory.memory_type == memory_type)
    stmt = stmt.order_by(OrgMemory.created_at.desc()).limit(limit)
    result = await session.execute(stmt)
    entries = result.scalars().all()
    return [
        MemorySearchResult(
            id=e.id, memory_type=e.memory_type, title=e.title,
            summary=e.summary, snippet=None, business_line=e.business_line,
            tags=e.tags, status=e.status, version=e.version,
            source_type=e.source_type, source_id=e.source_id,
            source_candidate_id=e.source_candidate_id,
            source_task_id=e.source_task_id,
            source_review_id=e.source_review_id,
            source_goal_session_id=e.source_goal_session_id,
            created_at=e.created_at,
        ) for e in entries
    ]


async def _fts5_search(
    session: AsyncSession,
    fts_query: str,
    business_line: str | None = None,
    memory_type: str | None = None,
    limit: int = 20,
) -> list[MemorySearchResult]:
    """FTS5 search — best for English/keyword queries, provides snippet."""
    sql = """
        SELECT o.id, o.memory_type, o.title, o.summary,
               snippet(org_memory_fts, 0, '<b>', '</b>', '...', 32) as snippet,
               o.business_line, o.tags, o.status, o.version,
               o.source_type, o.source_id,
               o.source_candidate_id, o.source_task_id,
               o.source_review_id, o.source_goal_session_id,
               o.created_at
        FROM org_memory_fts
        JOIN org_memory o ON o.id = org_memory_fts.rowid
        WHERE org_memory_fts MATCH :query
          AND o.status = 'active'
    """
    params: dict = {"query": fts_query}
    if business_line:
        sql += " AND o.business_line = :business_line"
        params["business_line"] = business_line
    if memory_type:
        sql += " AND o.memory_type = :memory_type"
        params["memory_type"] = memory_type
    sql += " ORDER BY rank LIMIT :limit"
    params["limit"] = limit

    result = await session.execute(text(sql), params)
    rows = result.fetchall()
    return [MemorySearchResult(**dict(row._mapping)) for row in rows]


@router.get("/search", response_model=list[MemorySearchResult])
async def search_memory(
    q: str,
    business_line: Optional[str] = None,
    memory_type: Optional[str] = None,
    limit: int = 20,
    session: AsyncSession = Depends(get_async_session),
):
    """Full-text search across OrgMemory.

    Strategy: try FTS5 first (provides ranked results + snippet).
    If FTS5 returns 0 results or is unavailable, fall back to LIKE
    which handles Chinese characters properly.
    """
    if not q or not q.strip():
        return []

    # Phase 1: Try FTS5 (if available)
    if fts5_available():
        fts_query = sanitize_fts5_query(q)
        if fts_query:
            fts_results = await _fts5_search(session, fts_query, business_line, memory_type, limit)
            if fts_results:
                return fts_results

    # Phase 2: LIKE fallback — handles Chinese text that FTS5 can't tokenize
    return await _like_search(session, q, business_line, memory_type, limit)
