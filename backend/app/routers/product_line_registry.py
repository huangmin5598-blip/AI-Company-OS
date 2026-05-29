# @PRODUCT Router — v0.10 Product Line Registry
from fastapi import APIRouter, HTTPException
from app.database import get_sync_session
from app.models.product_line_registry import ProductLineRegistry

router = APIRouter(prefix="/api/v1/product-lines", tags=["product-lines"])


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
        pl = ProductLineRegistry(**{k: data.get(k) for k in [
            "product_line_id", "name", "description", "owner_agent", "status", "related_skills",
        ] if k in data})
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
        for key in ["name", "description", "owner_agent", "status", "related_skills"]:
            if key in data:
                setattr(pl, key, data[key])
        session.commit()
        return pl.to_dict()
    finally:
        session.close()
