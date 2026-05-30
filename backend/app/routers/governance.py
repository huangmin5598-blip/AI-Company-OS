"""v0.16 — Governance Router

Exposes Runtime Health Check, Cost Summary, and Budget Check endpoints.
"""
from fastapi import APIRouter, HTTPException
from app.services.runtime_health import check_all, check_runtime
from app.services.cost_summary import scan_all, cost_report_markdown
from app.services.budget_guard import check_work_order

router = APIRouter(prefix="/api/v1/governance", tags=["governance"])


@router.get("/health")
async def health_check():
    """Run health checks for all registered runtimes.

    Returns dict mapping runtime name → health status.
    """
    results = check_all()
    return {
        "results": {name: r.to_dict() for name, r in results.items()},
        "all_healthy": all(r.status != "unhealthy" for r in results.values()),
    }


@router.get("/health/{runtime}")
async def health_check_runtime(runtime: str):
    """Check health of a specific runtime (openclaw, codex, local_llm)."""
    result = check_runtime(runtime)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Unknown runtime: {runtime}")
    return result.to_dict()


@router.get("/cost-summary")
async def cost_summary():
    """Get aggregated cost summary across all Work Orders.

    Returns total tokens, estimated cost, and breakdowns by agent, runtime, skill.
    Note: All costs are estimated, not actual billing.
    """
    summary = scan_all()
    return summary.to_dict()


@router.get("/cost-report")
async def cost_report():
    """Get cost summary as Markdown report."""
    return {"report": cost_report_markdown()}


@router.post("/budget-check")
async def budget_check(data: dict):
    """Check if a Work Order's token usage exceeds budget thresholds.

    Body: {"total_tokens": 15000, "skill_id": "research_summary"}
    Returns violations (if any). This is a soft guard, no hard kill.
    """
    total = data.get("total_tokens", 0)
    skill_id = data.get("skill_id", "")
    result = check_work_order(total, skill_id=skill_id)
    return result.to_dict()
