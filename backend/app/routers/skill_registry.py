# @PRODUCT Router — v0.10 Skill Registry
from fastapi import APIRouter, HTTPException
from app.database import get_sync_session
from app.models.skill_registry import SkillRegistry

router = APIRouter(prefix="/api/v1/skills", tags=["skills"])


@router.get("")
async def list_skills(capability_type: str = "", status: str = ""):
    """List all registered skills."""
    session = get_sync_session()
    try:
        q = session.query(SkillRegistry)
        if capability_type:
            q = q.filter_by(capability_type=capability_type)
        if status:
            q = q.filter_by(status=status)
        skills = q.all()
        return {"skills": [s.to_dict() for s in skills]}
    finally:
        session.close()


@router.post("")
async def create_skill(data: dict):
    """Register a new skill."""
    session = get_sync_session()
    try:
        existing = session.query(SkillRegistry).filter_by(skill_id=data["skill_id"]).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Skill '{data['skill_id']}' already exists")
        skill = SkillRegistry(**{k: data.get(k) for k in [
            "skill_id", "name", "description", "capability_type",
            "owner_agent", "owner_runtime", "risk_level", "execution_mode",
            "input_schema", "output_schema", "examples", "status",
        ] if k in data})
        session.add(skill)
        session.commit()
        return skill.to_dict()
    finally:
        session.close()


@router.get("/{skill_id}")
async def get_skill(skill_id: str):
    session = get_sync_session()
    try:
        skill = session.query(SkillRegistry).filter_by(skill_id=skill_id).first()
        if not skill:
            raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")
        return skill.to_dict()
    finally:
        session.close()


@router.patch("/{skill_id}")
async def update_skill(skill_id: str, data: dict):
    session = get_sync_session()
    try:
        skill = session.query(SkillRegistry).filter_by(skill_id=skill_id).first()
        if not skill:
            raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")
        for key in ["name", "description", "capability_type", "owner_agent",
                     "owner_runtime", "risk_level", "execution_mode",
                     "input_schema", "output_schema", "examples", "status"]:
            if key in data:
                setattr(skill, key, data[key])
        session.commit()
        return skill.to_dict()
    finally:
        session.close()
