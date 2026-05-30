"""v0.16 — Failure Policy

Defines how Work Order failures are classified and handled.

Rules:
  unknown_task_type     → needs_review
  runtime_unhealthy     → needs_review
  executor_timeout      → timeout + needs_review
  openclaw_cli_error    → failed + needs_review
  json_parse_error      → failed + needs_review
  tool_trace_missing    → warning (not failure)
  consecutive_failures  → escalation_required

Retry:
  low risk + idempotent task  → max 1 retry
  medium/high risk             → no retry, direct needs_review
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class FailureCode(Enum):
    UNKNOWN_TASK_TYPE = "unknown_task_type"
    RUNTIME_UNHEALTHY = "runtime_unhealthy"
    EXECUTOR_TIMEOUT = "executor_timeout"
    OPENCLAW_CLI_ERROR = "openclaw_cli_error"
    JSON_PARSE_ERROR = "json_parse_error"
    TOOL_TRACE_MISSING = "tool_trace_missing"
    CONSECUTIVE_FAILURES = "consecutive_failures"
    BUDGET_EXCEEDED = "budget_exceeded"
    MISSING_REQUIRED_FIELD = "missing_required_field"


class FailureAction(Enum):
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"
    TIMEOUT = "timeout"
    WARNING = "warning"
    RETRY = "retry"
    ESCALATE = "escalation_required"


@dataclass
class FailureDecision:
    code: FailureCode
    action: FailureAction
    reason: str
    can_retry: bool = False
    retry_count: int = 0
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "failure_code": self.code.value,
            "action": self.action.value,
            "reason": self.reason,
            "can_retry": self.can_retry,
            "retry_count": self.retry_count,
            "details": self.details,
        }

    def to_manifest_update(self) -> dict:
        """Return fields to add to ExecutionResult/Result Manifest."""
        return {
            "failure_code": self.code.value,
            "failure_action": self.action.value,
            "failure_reason": self.reason,
        }


# ── Policy Rules ──


MAX_RETRIES_LOW_RISK = 1


def classify(task_type: str, risk_level: str, attempt_count: int,
             executor_result: Optional[dict] = None,
             health_status: Optional[dict] = None) -> FailureDecision:
    """Classify a Work Order execution outcome into a FailureDecision.

    Args:
        task_type: The task type attempted.
        risk_level: low/medium/high.
        attempt_count: Number of attempts so far (1 = first try).
        executor_result: Optional dict with executor_type, status, error.
        health_status: Optional dict with runtime health status.

    Returns:
        FailureDecision with code, action, reason.
    """
    risk_level = (risk_level or "low").strip().lower()

    # 1. Unknown task type
    if task_type and task_type.startswith("unknown_"):
        return FailureDecision(
            code=FailureCode.UNKNOWN_TASK_TYPE,
            action=FailureAction.NEEDS_REVIEW,
            reason=f"Unknown task type '{task_type}'. No matching skill in registry.",
        )

    # 2. Runtime unhealthy
    if health_status:
        unhealthy = [name for name, s in health_status.items() if s == "unhealthy"]
        if unhealthy:
            return FailureDecision(
                code=FailureCode.RUNTIME_UNHEALTHY,
                action=FailureAction.NEEDS_REVIEW,
                reason=f"Runtime(s) unhealthy: {', '.join(unhealthy)}. Cannot execute.",
                details={"unhealthy_runtimes": unhealthy},
            )

    # 3. Executor timeout
    if executor_result:
        e_type = executor_result.get("executor_type", "")
        e_status = executor_result.get("status", "")
        e_error = executor_result.get("error_message", "")

        if "timeout" in e_error.lower() or "timed out" in e_error.lower():
            # Low risk + first attempt → 1 retry
            can_retry = risk_level == "low" and attempt_count <= MAX_RETRIES_LOW_RISK
            return FailureDecision(
                code=FailureCode.EXECUTOR_TIMEOUT,
                action=FailureAction.RETRY if can_retry else FailureAction.NEEDS_REVIEW,
                reason=f"Executor timed out after timeout period. {'Retrying...' if can_retry else 'Needs review.'}",
                can_retry=can_retry,
                retry_count=attempt_count,
            )

        # 4. CLI error
        if e_status == "failed" and e_type == "openclaw_agent":
            return FailureDecision(
                code=FailureCode.OPENCLAW_CLI_ERROR,
                action=FailureAction.NEEDS_REVIEW,
                reason=f"OpenClaw CLI execution failed: {e_error[:200] if e_error else 'Unknown error'}",
            )

        # 5. JSON parse error
        if e_status == "needs_review" and "non-JSON" in e_error.lower():
            return FailureDecision(
                code=FailureCode.JSON_PARSE_ERROR,
                action=FailureAction.NEEDS_REVIEW,
                reason=f"OpenClaw returned non-JSON output: {e_error[:200] if e_error else 'Unknown'}",
            )

    # 6. Consecutive failures
    if attempt_count > 2:
        return FailureDecision(
            code=FailureCode.CONSECUTIVE_FAILURES,
            action=FailureAction.ESCALATE,
            reason=f"Work Order failed {attempt_count} times consecutively. Escalating to Founder.",
            retry_count=attempt_count,
        )

    # Default: needs_review
    return FailureDecision(
        code=FailureCode.MISSING_REQUIRED_FIELD,
        action=FailureAction.NEEDS_REVIEW,
        reason=f"Unhandled failure or missing execution result.",
    )
