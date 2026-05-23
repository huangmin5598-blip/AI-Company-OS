"""Router for memory recall (CEO Agent专用) — Chinese-friendly FTS5 + multi-field fallback."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, or_
import re
import logging

from app.database import get_async_session
from app.models.org_memory import OrgMemory
from app.schemas.memory_recall import MemoryRecallRequest, MemoryRecallResponse, RecalledMemory
from app.models.fts_triggers import fts5_available
from app.routers.memory_search import sanitize_fts5_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


def extract_cjk_keywords(text: str, max_terms: int = 3) -> list[str]:
    """Extract keyword fragments from Chinese text without NLP dependency.
    
    Splits by common Chinese punctuation and returns non-empty fragments.
    """
    fragments = re.split(r'[\/，。、！？\s,.]', text)
    return [f.strip() for f in fragments if len(f.strip()) >= 2][:max_terms]


@router.post("/recall", response_model=MemoryRecallResponse)
async def recall_memory(
    body: MemoryRecallRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """Recall relevant org_memory entries for CEO Agent Goal Intake.
    
    Chinese-friendly strategy:
    1. Full goal_summary + business_line search (FTS5 or LIKE)
    2. If < 3 results, extract CJK keyword fragments and re-search
    3. Return top 3, deduplicated
    
    Empty results do NOT block CEO Agent — return [] gracefully.
    """
    goal = body.goal_summary.strip()
    business_line = body.business_line
    if not goal:
        return MemoryRecallResponse(memories=[], recall_query="", total=0)

    # Collect candidate memories
    candidates: list[dict] = []
    seen_ids: set[int] = set()

    def add_if_not_seen(memories: list):
        for m in memories:
            if m.get("memory_id") not in seen_ids:
                seen_ids.add(m["memory_id"])
                candidates.append(m)

    # --- Phase 1: Full goal_summary search ---
    top = await _fts_or_like_search(session, goal, business_line, limit=5)
    add_if_not_seen(top)

    # --- Phase 2: CJK keyword fragments (if < 3 results) ---
    if len(candidates) < 3:
        keywords = extract_cjk_keywords(goal)
        for kw in keywords:
            if kw == goal:
                continue
            more = await _fts_or_like_search(session, kw, business_line, limit=5)
            add_if_not_seen(more)
            if len(candidates) >= 3:
                break

    # --- Phase 3: Business-line-only search (if still < 3) ---
    if len(candidates) < 3 and business_line:
        line_only = await _fts_or_like_search(session, business_line, None, limit=5)
        add_if_not_seen(line_only)

    # Sort by confidence desc, take top 3
    candidates.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)
    top3 = candidates[:3]

    return MemoryRecallResponse(
        memories=[RecalledMemory(**m) for m in top3],
        recall_query=goal,
        total=len(top3),
    )


async def _fts_or_like_search(
    session: AsyncSession,
    query: str,
    business_line: str | None,
    limit: int = 5,
) -> list[dict]:
    """Internal: search OrgMemory with FTS5 first, then LIKE fallback for Chinese."""
    if not query or not query.strip():
        return []

    # Phase 1: Try FTS5
    if fts5_available():
        fts_q = sanitize_fts5_query(query)
        if fts_q:
            sql = """
                SELECT o.id, o.title, o.summary, o.memory_type, o.confidence
                FROM org_memory_fts
                JOIN org_memory o ON o.id = org_memory_fts.rowid
                WHERE org_memory_fts MATCH :query AND o.status = 'active'
            """
            params: dict = {"query": fts_q}
            if business_line:
                sql += " AND o.business_line = :business_line"
                params["business_line"] = business_line
            sql += " ORDER BY rank LIMIT :limit"
            params["limit"] = limit

            result = await session.execute(text(sql), params)
            rows = result.fetchall()
            if rows:
                return [
                    {
                        "memory_id": r.id,
                        "title": r.title,
                        "summary": r.summary,
                        "memory_type": r.memory_type,
                        "confidence": r.confidence or 0.7,
                    }
                    for r in rows
                ]

    # Phase 2: LIKE fallback (handles Chinese that FTS5 can't tokenize)
    stmt = select(OrgMemory).where(
        OrgMemory.status == "active",
        or_(
            OrgMemory.title.ilike(f"%{query}%"),
            OrgMemory.summary.ilike(f"%{query}%"),
            OrgMemory.content.ilike(f"%{query}%"),
            OrgMemory.tags.ilike(f"%{query}%"),
        ),
    )
    if business_line:
        stmt = stmt.where(OrgMemory.business_line == business_line)
    stmt = stmt.order_by(OrgMemory.created_at.desc()).limit(limit)
    result = await session.execute(stmt)
    entries = result.scalars().all()
    return [
        {
            "memory_id": e.id,
            "title": e.title,
            "summary": e.summary,
            "memory_type": e.memory_type,
            "confidence": e.confidence or 0.7,
        }
        for e in entries
    ]
