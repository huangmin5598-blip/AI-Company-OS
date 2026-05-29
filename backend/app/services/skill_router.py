# @PRODUCT Service — v0.10 Skill Router (Deterministic)
"""
Skill Router — 确定性路由引擎。

输入 task_type → 映射到 capability_type → 查询 Skill Registry → 返回匹配 skill。
LLM 不参与低层路由。所有规则在 Python 中完成。
"""
from app.database import get_sync_session
from app.models.skill_registry import SkillRegistry


TASK_TYPE_TO_CAPABILITY = {
    # 研究类
    "research": "research",
    "market_analysis": "research",
    "competitor_analysis": "research",
    "user_research": "research",
    # 文案类
    "copywriting": "copywriting",
    "landing_page_copy": "copywriting",
    "marketing_copy": "copywriting",
    "content_writing": "copywriting",
    # 代码类
    "code_build": "code_build",
    "landing_page_code": "code_build",
    "feature_implementation": "code_build",
    "page_generation": "code_build",
    # 报告类
    "report_generation": "report_generation",
    "profit_health_report": "report_generation",
    "business_report": "report_generation",
    # 部署类
    "deploy": "deploy",
    "deployment_checklist": "deploy",
    "publish": "deploy",
    # 外部交互类 (v0.13 — OpenClaw 执行)
    "customer_response": "external_interaction",
    "customer_support": "external_interaction",
    "external_data": "external_interaction",
}


def route(task_type: str) -> dict:
    """
    路由查询：输入 task_type → 返回匹配的 skill 信息。

    返回：
        {"skill_id": ..., "runtime_id": ..., "risk_level": ..., "execution_mode": ...}
        或 {"error": "no_matching_skill", "reason": "..."}
    """
    capability = TASK_TYPE_TO_CAPABILITY.get(task_type)
    if not capability:
        return {
            "error": "no_matching_skill",
            "reason": f"Unknown task_type: '{task_type}'. Known types: {', '.join(sorted(set(TASK_TYPE_TO_CAPABILITY.values())))}",
        }

    session = get_sync_session()
    try:
        skill = session.query(SkillRegistry).filter_by(
            capability_type=capability,
            status="active",
        ).first()

        if not skill:
            return {
                "error": "no_matching_skill",
                "reason": f"No active skill for capability '{capability}'",
            }

        return {
            "skill_id": skill.skill_id,
            "name": skill.name,
            "capability_type": skill.capability_type,
            "owner_agent": skill.owner_agent,
            "runtime_id": skill.owner_runtime,
            "risk_level": skill.risk_level,
            "execution_mode": skill.execution_mode,
        }
    finally:
        session.close()


def batch_route(tasks: list[dict]) -> list[dict]:
    """
    批量路由：输入 [{task_type, task_desc}, ...]
    输出 [{task_type, skill_id, runtime_id, risk_level, execution_mode}, ...]
    """
    results = []
    for task in tasks:
        task_type = task.get("task_type", "")
        result = route(task_type)
        results.append({
            "task_type": task_type,
            "task_desc": task.get("task_desc", ""),
            **result,
        })
    return results


def get_available_capabilities() -> list[str]:
    """返回所有可用的 capability_type 列表"""
    session = get_sync_session()
    try:
        caps = session.query(SkillRegistry.capability_type).filter_by(
            status="active"
        ).distinct().all()
        return [c[0] for c in caps]
    finally:
        session.close()
