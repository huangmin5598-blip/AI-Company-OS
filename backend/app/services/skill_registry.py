"""v0.15 — Skill Registry Loader

Loads skill definitions from YAML config and provides routing contracts.

Architecture:
  1. skill_registry.yaml  →  single source of truth
  2. load() / get_contract()  →  runtime lookup
  3. Unknown task_type  →  needs_review contract
"""
import os
import sys
from typing import Optional

import yaml

# Path to YAML config (relative to backend/)
_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "config", "skill_registry.yaml")


class RoutingContract:
    """Routing decision for one Work Order."""

    def __init__(
        self,
        skill_id: str,
        description: str,
        default_agent: str,
        runtime: str,
        executor: str,
        risk_level: str,
        approval_required: bool,
        output_schema: str,
        routing_reason: str,
        allowed_tools: Optional[list] = None,
        budget_class: str = "",
    ):
        self.skill_id = skill_id
        self.description = description
        self.default_agent = default_agent
        self.runtime = runtime
        self.executor = executor
        self.risk_level = risk_level
        self.approval_required = approval_required
        self.output_schema = output_schema
        self.routing_reason = routing_reason
        self.allowed_tools = allowed_tools or []
        self.budget_class = budget_class

    def to_dict(self) -> dict:
        return {
            "skill_id": self.skill_id,
            "description": self.description,
            "default_agent": self.default_agent,
            "runtime": self.runtime,
            "executor": self.executor,
            "risk_level": self.risk_level,
            "approval_required": self.approval_required,
            "output_schema": self.output_schema,
            "routing_reason": self.routing_reason,
            "allowed_tools": self.allowed_tools,
            "budget_class": self.budget_class,
        }


def _fatal(msg: str):
    """Print error and exit — YAML config is boot-critical."""
    print(f"[skill_registry] FATAL: {msg}", file=sys.stderr)
    sys.exit(1)


# ── Public: Canonical Result ──

ROUTING_OK = "ok"
ROUTING_UNKNOWN = "needs_review"


class SkillRegistryResult:
    """Result of a routing lookup."""

    def __init__(self, status: str, contract: Optional[RoutingContract] = None, reason: str = ""):
        self.status = status          # "ok" | "needs_review"
        self.contract = contract      # None if unknown
        self.reason = reason          # human-readable routing explanation

    def to_dict(self) -> dict:
        d = {
            "status": self.status,
            "reason": self.reason,
        }
        if self.contract:
            d.update(self.contract.to_dict())
        return d


# ── Loader ──

_loaded: Optional[dict[str, RoutingContract]] = None
"""Cache: task_type → RoutingContract"""


def _build_cache(skills: list[dict]) -> dict[str, RoutingContract]:
    """Build task_type → RoutingContract lookup from parsed YAML."""
    cache: dict[str, RoutingContract] = {}
    for skill in skills:
        sid = skill.get("skill_id", "")
        if not sid:
            _fatal("Skill missing 'skill_id'")
        task_types = skill.get("task_types", [])
        if not task_types:
            _fatal(f"Skill '{sid}' has empty 'task_types'")
        for ttype in task_types:
            if ttype in cache:
                _fatal(f"Task type '{ttype}' mapped by multiple skills: '{cache[ttype].skill_id}' and '{sid}'")
            cache[ttype] = RoutingContract(
                skill_id=sid,
                description=skill.get("description", ""),
                default_agent=skill.get("default_agent", ""),
                runtime=skill.get("runtime", ""),
                executor=skill.get("executor", ""),
                risk_level=skill.get("risk_level", "low"),
                approval_required=bool(skill.get("approval_required", False)),
                output_schema=skill.get("output_schema", ""),
                allowed_tools=skill.get("allowed_tools", []),
                budget_class=skill.get("budget_class", ""),
                routing_reason="",  # Set per-call in get_contract
            )
    return cache


def load(force_reload: bool = False) -> dict[str, RoutingContract]:
    """Load (or reload) the skill registry from YAML.

    Returns:
        dict mapping task_type → RoutingContract
    """
    global _loaded
    if _loaded is not None and not force_reload:
        return _loaded

    if not os.path.exists(_CONFIG_PATH):
        _fatal(f"Skill registry YAML not found at {_CONFIG_PATH}")

    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if not raw or "skills" not in raw:
        _fatal("YAML missing 'skills' key")

    skills = raw["skills"]
    if not isinstance(skills, list) or len(skills) == 0:
        _fatal("'skills' must be a non-empty list")

    _loaded = _build_cache(skills)
    print(f"[skill_registry] Loaded {len(skills)} skills ({len(_loaded)} task types)")
    return _loaded


def get_contract(task_type: str) -> SkillRegistryResult:
    """Look up routing contract for a task type.

    Returns:
        SkillRegistryResult with status "ok" or "needs_review".
    """
    cache = load()
    contract = cache.get(task_type)
    if contract is None:
        return SkillRegistryResult(
            status=ROUTING_UNKNOWN,
            reason=f"Unknown task_type '{task_type}'. No matching skill in registry.",
        )

    # Build per-call routing reason
    contract.routing_reason = (
        f"task_type '{task_type}' → skill '{contract.skill_id}' "
        f"(agent={contract.default_agent}, runtime={contract.runtime}, "
        f"risk={contract.risk_level})"
    )

    return SkillRegistryResult(status=ROUTING_OK, contract=contract)


def list_skills() -> list[dict]:
    """List all registered skills (for API / diagnostics)."""
    cache = load()
    seen: dict[str, RoutingContract] = {}
    for contract in cache.values():
        seen[contract.skill_id] = contract
    return [c.to_dict() for c in seen.values()]


def list_task_types() -> list[str]:
    """List all registered task types."""
    cache = load()
    return sorted(cache.keys())


# ── Auto-load at import time ──
# Fail fast: if YAML is missing or malformed, crash on import.
load()
