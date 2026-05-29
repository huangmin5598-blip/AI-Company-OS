# @PRODUCT Router — v0.12 Product Line Registry (Agent Boundaries)
from fastapi import APIRouter, HTTPException
from app.database import get_sync_session
from app.models.product_line_registry import ProductLineRegistry

router = APIRouter(prefix="/api/v1/product-lines", tags=["product-lines"])

ALL_FIELDS = [
    "product_line_id", "name", "description", "owner_agent", "status",
    "related_skills", "scope", "current_goal", "active_projects", "weekly_status",
]


@router.get("")
async def list_product_lines():
    session = get_sync_session()
    try:
        lines = session.query(ProductLineRegistry).all()
        return {"product_lines": [l.to_dict() for l in lines]}
    finally:
        session.close()


@router.get("/{product_line_id}")
async def get_product_line(product_line_id: str):
    session = get_sync_session()
    try:
        pl = session.query(ProductLineRegistry).filter_by(product_line_id=product_line_id).first()
        if not pl:
            raise HTTPException(status_code=404, detail=f"Product line '{product_line_id}' not found")
        return pl.to_dict()
    finally:
        session.close()


@router.post("")
async def create_product_line(data: dict):
    session = get_sync_session()
    try:
        existing = session.query(ProductLineRegistry).filter_by(product_line_id=data["product_line_id"]).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Product line '{data['product_line_id']}' already exists")
        pl = ProductLineRegistry(**{k: data.get(k) for k in ALL_FIELDS if k in data})
        session.add(pl)
        session.commit()
        return pl.to_dict()
    finally:
        session.close()


@router.patch("/{product_line_id}")
async def update_product_line(product_line_id: str, data: dict):
    session = get_sync_session()
    try:
        pl = session.query(ProductLineRegistry).filter_by(product_line_id=product_line_id).first()
        if not pl:
            raise HTTPException(status_code=404, detail=f"Product line '{product_line_id}' not found")
        for key in ALL_FIELDS:
            if key in data:
                setattr(pl, key, data[key])
        session.commit()
        return pl.to_dict()
    finally:
        session.close()


# ── v0.12: Product Line Status Summary ──

@router.get("/summary/status")
async def product_line_status_summary():
    """Return a compact CEO-view summary of all product lines.

    Used by the CEO Orchestrator for weekly status reporting.
    """
    session = get_sync_session()
    try:
        lines = session.query(ProductLineRegistry).all()
        summary = []
        for pl in lines:
            summary.append({
                "product_line_id": pl.product_line_id,
                "name": pl.name,
                "status": pl.status,
                "owner_agent": pl.owner_agent,
                "current_goal": pl.current_goal or "",
                "active_projects": pl.active_projects or "[]",
                "weekly_status": pl.weekly_status or "",
                "skill_count": len([s for s in (pl.related_skills or "").split(",") if s.strip()]),
            })
        return {
            "total_product_lines": len(summary),
            "active": len([s for s in summary if s["status"] == "active"]),
            "incubating": len([s for s in summary if s["status"] == "incubating"]),
            "paused": len([s for s in summary if s["status"] == "paused"]),
            "product_lines": summary,
        }
    finally:
        session.close()
