# @PRODUCT Router — v0.10 Skill Router (separate prefix to avoid path param conflict)
from fastapi import APIRouter, HTTPException
from app.services.skill_router import route, batch_route, get_available_capabilities

router = APIRouter(prefix="/api/v1/router", tags=["skill-router"])


@router.get("/route")
async def route_skill(task_type: str):
    """
    Skill Router — 输入 task_type，返回匹配的 skill。
    确定性规则，不用 LLM。
    """
    result = route(task_type)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result)
    return result


@router.post("/batch-route")
async def batch_route_skills(tasks: list[dict]):
    """批量路由：输入 [{task_type, task_desc}, ...]"""
    results = batch_route(tasks)
    return {"routes": results}


@router.get("/capabilities")
async def list_capabilities():
    """列出所有可用的能力类型。"""
    caps = get_available_capabilities()
    return {"capabilities": caps}
