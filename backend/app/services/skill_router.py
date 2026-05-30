"""v0.15 — Skill Router (YAML-backed)

Routes task_type → skill_id via the YAML-based Skill Registry.
Replaces the old hardcoded TASK_TYPE_TO_CAPABILITY dict + DB table approach.

Unknown task_type → needs_review (status='blocked', reason='unknown_task_type').
"""
from app.services.skill_registry import get_contract, ROUTING_UNKNOWN


# ── Compat mapping: old API callers expect specific fields ──

_COMPAT_FIELD_MAP = {
    "default_agent": "owner_agent",
    "runtime": "runtime_id",
    "executor": "execution_mode",
    "skill_id": "skill_id",
    "risk_level": "risk_level",
    "approval_required": "approval_required",
    "output_schema": "output_schema",
}


def route(task_type: str) -> dict:
    """Route a task type to a skill.

    Returns dict with keys:
      - skill_id, owner_agent, runtime_id, execution_mode, risk_level,
        approval_required, output_schema, routing_reason, capability_type
      - OR {"error": "no_matching_skill", "reason": "..."} for unknown types

    Compat: returns same field names as old DB-backed router.
    """
    result = get_contract(task_type)

    if result.status == ROUTING_UNKNOWN:
        return {
            "error": "no_matching_skill",
            "reason": result.reason,
            "status": "needs_review",
            "routing_reason": result.reason,
        }

    contract = result.contract
    routing_dict = {
        "skill_id": contract.skill_id,
        "name": contract.skill_id,
        "description": contract.description,
        "owner_agent": contract.default_agent,
        "runtime_id": contract.runtime,
        "execution_mode": contract.executor,
        "risk_level": contract.risk_level,
        "approval_required": contract.approval_required,
        "output_schema": contract.output_schema,
        "allowed_tools": contract.allowed_tools,
        "budget_class": contract.budget_class,
        "routing_reason": contract.routing_reason,
        "capability_type": contract.skill_id,  # compat: old callers expect this
        "status": "ok",
    }
    return routing_dict


def batch_route(tasks: list[dict]) -> list[dict]:
    """Batch route multiple tasks."""
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
    """Return all registered skill IDs."""
    from app.services.skill_registry import list_skills
    return [s["skill_id"] for s in list_skills()]
