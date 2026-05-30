"""v0.16 — Soft Budget Guard

Lightweight budget threshold checks. No hard kill, no billing.

Reads budget policy from YAML config. Compares actual usage against
per-skill and default thresholds. Returns warning or needs_review.

Config: backend/config/budget_policy.yaml (loaded at runtime)
"""
import os
from dataclasses import dataclass, field
from typing import Optional

import yaml

# Path to YAML (relative to backend/)
_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "config", "budget_policy.yaml"
)


@dataclass
class BudgetViolation:
    threshold: str  # e.g. "max_tokens_per_work_order"
    limit: int
    actual: int
    action: str  # "warn" | "needs_review"
    message: str

    def to_dict(self) -> dict:
        return {
            "threshold": self.threshold,
            "limit": self.limit,
            "actual": self.actual,
            "action": self.action,
            "message": self.message,
        }


@dataclass
class BudgetCheckResult:
    passed: bool
    violations: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "violations": [v.to_dict() for v in self.violations],
        }


# ── Default policy (used when YAML is missing) ──

_DEFAULT_POLICY = {
    "default": {
        "max_tokens_per_work_order": 20000,
        "max_tokens_per_run": 100000,
        "max_tokens_per_day": 200000,
        "action_on_exceed": "needs_review",
    },
    "research_summary": {
        "max_tokens_per_work_order": 60000,
        "max_tokens_per_run": 120000,
        "action_on_exceed": "warn",
    },
    "code_change": {
        "max_tokens_per_work_order": 50000,
        "action_on_exceed": "needs_review",
    },
}


# ── Loader ──

_loaded_policy: Optional[dict] = None


def load_policy(force_reload: bool = False) -> dict:
    """Load budget policy from YAML or fallback to defaults."""
    global _loaded_policy
    if _loaded_policy is not None and not force_reload:
        return _loaded_policy

    if os.path.exists(_CONFIG_PATH):
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f)
            if raw and "budget_policy" in raw:
                _loaded_policy = raw["budget_policy"]
                print(f"[budget_policy] Loaded from {_CONFIG_PATH}")
                return _loaded_policy
        except Exception as e:
            print(f"[budget_policy] Failed to load {_CONFIG_PATH}: {e}")

    _loaded_policy = _DEFAULT_POLICY
    print(f"[budget_policy] Using defaults (no YAML at {_CONFIG_PATH})")
    return _loaded_policy


# ── Check ──


def check_work_order(total_tokens: int, skill_id: str = "",
                     product_line: str = "",
                     scope: str = "per_work_order") -> BudgetCheckResult:
    """Check if a Work Order's token usage exceeds budget thresholds.

    Args:
        total_tokens: Total tokens used (scope-dependent).
        skill_id: Skill ID for skill-specific thresholds.
        product_line: Product line (future: per-line budget).
        scope: Budget scope — "per_work_order" | "current_run" | "daily" | "lifetime".
            - per_work_order: compares against skill's per-WO threshold
            - current_run: compares against per-run threshold
            - daily: compares against daily threshold
            - lifetime: DISPLAY ONLY — never triggers a warning

    Returns:
        BudgetCheckResult with violations (if any).
    """
    policy = load_policy()
    violations = []

    # Lifetime scope — display only, never warns
    if scope == "lifetime":
        return BudgetCheckResult(passed=True, violations=[])

    # Resolve applicable policy: skill-specific > default
    skill_policy = policy.get(skill_id, {})
    default_policy = policy.get("default", {})

    if scope == "per_work_order":
        max_val = skill_policy.get(
            "max_tokens_per_work_order",
            default_policy.get("max_tokens_per_work_order", 20000),
        )
        action = skill_policy.get(
            "action_on_exceed",
            default_policy.get("action_on_exceed", "needs_review"),
        )
        threshold_name = "max_tokens_per_work_order"
    elif scope == "current_run":
        max_val = default_policy.get("max_tokens_per_run", 50000)
        action = default_policy.get("action_on_exceed", "needs_review")
        threshold_name = "max_tokens_per_run"
    elif scope == "daily":
        max_val = default_policy.get("max_tokens_per_day", 100000)
        action = "needs_review"
        threshold_name = "max_tokens_per_day"
    else:
        return BudgetCheckResult(passed=True, violations=[])

    if total_tokens > max_val:
        violations.append(BudgetViolation(
            threshold=threshold_name,
            limit=max_val,
            actual=total_tokens,
            action=action,
            message=(
                f"Token usage {total_tokens:,} exceeds {threshold_name} "
                f"budget {max_val:,} (scope={scope}). "
                f"Action: {action}."
            ),
        ))

    return BudgetCheckResult(
        passed=len(violations) == 0,
        violations=violations,
    )


def check_total(total_tokens: int, runtime: str = "") -> BudgetCheckResult:
    """Check if total accumulated usage exceeds per-day budget."""
    policy = load_policy()
    default_policy = policy.get("default", {})
    max_per_day = default_policy.get("max_tokens_per_day", 100000)

    violations = []
    if total_tokens > max_per_day:
        violations.append(BudgetViolation(
            threshold="max_tokens_per_day",
            limit=max_per_day,
            actual=total_tokens,
            action="needs_review",
            message=f"Total token usage {total_tokens:,} exceeds daily budget {max_per_day:,}.",
        ))

    return BudgetCheckResult(passed=len(violations) == 0, violations=violations)
