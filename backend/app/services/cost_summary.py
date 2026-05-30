"""v0.16 — Cost Summary

Aggregates token usage and estimated cost from Result Manifests.

Data sources: result.json files in ~/.ai-company-os/artifacts/<WO-ID>/
Aggregates by: work_order, agent, runtime, skill, product_line.

Note: These are ESTIMATED costs based on token counts.
Actual cost depends on provider pricing which may vary.
"""
import json
import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Artifacts directory
BASE_ARTIFACTS_DIR = os.path.expanduser("~/.ai-company-os/artifacts")

# Estimated cost per 1K tokens (USD) — rough estimates
# These are NOT provider-precise, just order-of-magnitude
COST_PER_1K_INPUT = {
    "MiniMax-M2.5": 0.002,
    "deepseek-r1:8b": 0.0,  # local = free
    "default": 0.003,
}
COST_PER_1K_OUTPUT = {
    "MiniMax-M2.5": 0.008,
    "deepseek-r1:8b": 0.0,
    "default": 0.012,
}


@dataclass
class WorkOrderCost:
    work_order_id: str
    skill_id: str
    agent: str
    runtime: str
    model_name: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    duration_ms: int = 0
    estimated_cost: float = 0.0

    def to_dict(self) -> dict:
        return {
            "work_order_id": self.work_order_id,
            "skill_id": self.skill_id,
            "agent": self.agent,
            "runtime": self.runtime,
            "model_name": self.model_name,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "duration_ms": self.duration_ms,
            "estimated_cost_usd": round(self.estimated_cost, 6),
        }


@dataclass
class CostSummary:
    total_tokens: int = 0
    total_estimated_cost: float = 0.0
    total_duration_ms: int = 0
    work_order_count: int = 0
    by_agent: dict = field(default_factory=lambda: defaultdict(lambda: {
        "work_orders": 0, "total_tokens": 0, "estimated_cost": 0.0, "duration_ms": 0,
    }))
    by_runtime: dict = field(default_factory=lambda: defaultdict(lambda: {
        "work_orders": 0, "total_tokens": 0, "estimated_cost": 0.0, "duration_ms": 0,
    }))
    by_skill: dict = field(default_factory=lambda: defaultdict(lambda: {
        "work_orders": 0, "total_tokens": 0, "estimated_cost": 0.0, "duration_ms": 0,
    }))

    def to_dict(self) -> dict:
        return {
            "total_tokens": self.total_tokens,
            "total_estimated_cost_usd": round(self.total_estimated_cost, 6),
            "total_duration_ms": self.total_duration_ms,
            "work_order_count": self.work_order_count,
            "by_agent": dict(self.by_agent) if self.by_agent else {},
            "by_runtime": dict(self.by_runtime) if self.by_runtime else {},
            "by_skill": dict(self.by_skill) if self.by_skill else {},
        }


def _resolve_result_path(wo_id: str) -> Optional[str]:
    """Find result.json for a work order ID."""
    path = os.path.join(BASE_ARTIFACTS_DIR, wo_id, "result.json")
    if os.path.isfile(path):
        return path
    return None


def _load_result(wo_id: str) -> Optional[dict]:
    """Load and parse result.json for a work order."""
    path = _resolve_result_path(wo_id)
    if not path:
        return None
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _get_cost_rate(model_name: str) -> tuple[float, float]:
    """Get estimated cost per 1K tokens for a model."""
    input_rate = COST_PER_1K_INPUT.get(model_name, COST_PER_1K_INPUT["default"])
    output_rate = COST_PER_1K_OUTPUT.get(model_name, COST_PER_1K_OUTPUT["default"])
    return input_rate, output_rate


def _estimate_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost in USD for a single execution."""
    input_rate, output_rate = _get_cost_rate(model_name)
    return (input_tokens / 1000.0 * input_rate) + (output_tokens / 1000.0 * output_rate)


def parse_work_order_cost(wo_id: str) -> Optional[WorkOrderCost]:
    """Parse a single Work Order's result manifest into a WorkOrderCost."""
    result = _load_result(wo_id)
    if not result:
        return None

    status = result.get("status", "")
    if status != "completed":
        return None

    tu = result.get("token_usage", {})
    input_tokens = tu.get("input_tokens", 0)
    output_tokens = tu.get("output_tokens", 0)
    total_tokens = tu.get("total_tokens", 0)

    # If total is empty, calculate from input+output
    if total_tokens == 0 and (input_tokens or output_tokens):
        total_tokens = input_tokens + output_tokens

    model_name = result.get("model_name", "default")
    agent = result.get("openclaw_agent", result.get("selected_agent", "unknown"))
    runtime = result.get("runtime_backend", "unknown")
    skill_id = result.get("skill_id", "")
    duration_ms = result.get("duration_ms", 0)

    cost = _estimate_cost(model_name, input_tokens, output_tokens)

    return WorkOrderCost(
        work_order_id=wo_id,
        skill_id=skill_id or "",
        agent=agent,
        runtime=runtime,
        model_name=model_name,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        duration_ms=duration_ms,
        estimated_cost=cost,
    )


def scan_all() -> CostSummary:
    """Scan all work order artifacts and compute cost summary."""
    if not os.path.isdir(BASE_ARTIFACTS_DIR):
        return CostSummary()

    summary = CostSummary()
    for entry in os.listdir(BASE_ARTIFACTS_DIR):
        wo_path = os.path.join(BASE_ARTIFACTS_DIR, entry)
        if not os.path.isdir(wo_path):
            continue
        if not entry.startswith("WO-"):
            continue

        woc = parse_work_order_cost(entry)
        if not woc:
            continue

        summary.total_tokens += woc.total_tokens
        summary.total_estimated_cost += woc.estimated_cost
        summary.total_duration_ms += woc.duration_ms
        summary.work_order_count += 1

        # By agent
        a = summary.by_agent[woc.agent]
        a["work_orders"] += 1
        a["total_tokens"] += woc.total_tokens
        a["estimated_cost"] += woc.estimated_cost
        a["duration_ms"] += woc.duration_ms

        # By runtime
        r = summary.by_runtime[woc.runtime]
        r["work_orders"] += 1
        r["total_tokens"] += woc.total_tokens
        r["estimated_cost"] += woc.estimated_cost
        r["duration_ms"] += woc.duration_ms

        # By skill
        sk = summary.by_skill[woc.skill_id or "unknown"]
        sk["work_orders"] += 1
        sk["total_tokens"] += woc.total_tokens
        sk["estimated_cost"] += woc.estimated_cost
        sk["duration_ms"] += woc.duration_ms

    # Round costs
    for group in [summary.by_agent, summary.by_runtime, summary.by_skill]:
        for key in group:
            group[key]["estimated_cost"] = round(group[key]["estimated_cost"], 6)

    return summary


def cost_report_markdown(summary: Optional[CostSummary] = None) -> str:
    """Generate a Markdown cost report."""
    if summary is None:
        summary = scan_all()

    lines = [
        "# Cost Summary Report",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Overview",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Work Orders | {summary.work_order_count} |",
        f"| Total Tokens | {summary.total_tokens:,} |",
        f"| Total Estimated Cost | \${summary.total_estimated_cost:.6f} |",
        f"| Total Duration | {summary.total_duration_ms / 1000:.1f}s |",
        "",
        "## By Agent",
        "| Agent | Work Orders | Tokens | Cost |",
        "|-------|-----------|--------|------|",
    ]
    for agent, data in sorted(summary.by_agent.items()):
        cost = summary.by_agent[agent]["estimated_cost"]
        lines.append(
            f"| {agent} | {data['work_orders']} | {data['total_tokens']:,} | \${cost:.6f} |"
        )

    lines.extend([
        "",
        "## By Runtime",
        "| Runtime | Work Orders | Tokens | Cost |",
        "|--------|-----------|--------|------|",
    ])
    for runtime, data in sorted(summary.by_runtime.items()):
        cost = summary.by_runtime[runtime]["estimated_cost"]
        lines.append(
            f"| {runtime} | {data['work_orders']} | {data['total_tokens']:,} | \${cost:.6f} |"
        )

    lines.extend([
        "",
        "## By Skill",
        "| Skill | Work Orders | Tokens | Cost |",
        "|------|-----------|--------|------|",
    ])
    for skill, data in sorted(summary.by_skill.items()):
        cost = summary.by_skill[skill]["estimated_cost"]
        lines.append(
            f"| {skill} | {data['work_orders']} | {data['total_tokens']:,} | \${cost:.6f} |"
        )

    lines.append("")
    lines.append("_Note: All costs are estimated. Actual provider billing may differ._")
    return "\n".join(lines)
