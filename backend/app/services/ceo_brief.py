"""v0.17 — CEO Brief Markdown Generator.

Aggregates governance data and execution results into a structured
CEO Brief report saved to reports/ceo-briefs/YYYY-MM-DD.md.
"""

import os
from datetime import datetime, date
from typing import Optional

from app.services.runtime_health import check_all, HealthResult
from app.services.cost_summary import scan_all, CostSummary

_REPORTS_DIR = os.path.expanduser(
    "~/Documents/Codex/ai-company-os/reports/ceo-briefs"
)


# ── Helpers ──


def _ensure_reports_dir():
    """Create reports/ceo-briefs/ if it doesn't exist."""
    os.makedirs(_REPORTS_DIR, exist_ok=True)


def _health_table(results: dict[str, HealthResult]) -> str:
    """Build a Markdown table from health check results."""
    lines = ["| Runtime | Status | Details |", "|---------|--------|---------|"]
    for name, r in sorted(results.items()):
        detail = ""
        if name == "openclaw":
            detail = f"v{r.details.get('version','?')}, agents={r.details.get('agent_count','?')}"
        elif name == "codex":
            detail = f"v{r.details.get('version','?')}"
        elif name == "local_llm":
            models = r.details.get("available_models", [])
            detail = f"{len(models)} models" if models else "no models"
        icon = "✅" if r.status == "healthy" else "❌"
        lines.append(f"| {name} | {icon} {r.status} | {detail} |")
    return "\n".join(lines)


def _cost_section(summary: CostSummary) -> str:
    """Build a Cost Summary section."""
    lines = [
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Work Orders | {summary.work_order_count} |",
        f"| Total Tokens | {summary.total_tokens:,} |",
        f"| Estimated Cost | ${summary.total_estimated_cost:.4f} |",
        f"| Total Duration | {summary.total_duration_ms / 1000:.1f}s |",
        "",
        "**By Agent:**",
    ]
    for agent, stats in sorted(summary.by_agent.items()):
        name = agent if agent else "(unassigned)"
        lines.append(f"- {name}: {stats['work_orders']} WOs, {stats['total_tokens']:,} tokens, ${stats['estimated_cost']:.4f}")

    lines.append("")
    lines.append("**By Runtime:**")
    for runtime, stats in sorted(summary.by_runtime.items()):
        name = runtime if runtime else "(unknown)"
        lines.append(f"- {name}: {stats['work_orders']} WOs, {stats['total_tokens']:,} tokens, ${stats['estimated_cost']:.4f}")

    return "\n".join(lines)


def _format_run_result(result: dict) -> str:
    """Format a single Work Order execution for the brief."""
    wo = result.get("work_order", {})
    exec_result = result.get("execution_result", {})
    status = wo.get("status", "?")
    icon = {"completed": "✅", "failed": "❌", "in_progress": "⏳",
            "requires_approval": "🛑"}.get(status, "❓")
    lines = [
        f"### {icon} {wo.get('work_order_id', '?')}",
        f"- **Status:** {status}",
        f"- **Skill:** {wo.get('skill_id', '?')}",
        f"- **Task:** {wo.get('task_type', '?')}",
        f"- **Agent:** {wo.get('assigned_agent', '?')}",
    ]
    error = wo.get("error", "") or exec_result.get("error", "")
    if error:
        lines.append(f"- **Error:** {error[:200]}")
    summary = exec_result.get("summary", "") or wo.get("result_summary", "")
    if summary:
        lines.append(f"- **Summary:** {summary[:300]}")
    if status == "failed":
        failure_code = exec_result.get("failure_code", "")
        if failure_code:
            lines.append(f"- **Failure Code:** {failure_code}")
    return "\n".join(lines)


# ── Brief Generator ──


def generate_brief(
    scheduled_id: str = "manual",
    today: Optional[date] = None,
    dry_run: bool = False,
    execution_results: Optional[list[dict]] = None,
    failures: Optional[list[dict]] = None,
    budget_warnings: Optional[list[str]] = None,
) -> str:
    """Generate a CEO Brief markdown document.

    Args:
        scheduled_id: Which scheduled task triggered this brief.
        today: Date for the brief (default: today).
        dry_run: If True, mark the brief as a dry run.
        execution_results: List of execute_work_order() return dicts.
        failures: List of failure manifest dicts.
        budget_warnings: List of budget warning descriptions.

    Returns:
        Full markdown content.
    """
    if today is None:
        today = date.today()
    _ensure_reports_dir()

    # Gather live data
    health_results = check_all()
    cost_summary = scan_all()
    all_healthy = all(r.status == "healthy" for r in health_results.values())
    any_unhealthy = [name for name, r in health_results.items() if r.status != "healthy"]

    # Count results
    results = execution_results or []
    failures = failures or []
    budget_warnings = budget_warnings or []

    completed = sum(
        1 for r in results
        if r.get("work_order", {}).get("status") == "completed"
    )
    failed = sum(
        1 for r in results
        if r.get("work_order", {}).get("status") in ("failed",)
    )
    needs_review = len(failures)

    # ── Build markdown ──
    lines = []
    lines.append(f"# CEO Daily Brief — {today.isoformat()}")
    if dry_run:
        lines.append("\n> ⚠️ **DRY RUN** — no Work Orders were actually executed.\n")
    if scheduled_id != "manual":
        lines.append(f"\n_Scheduled task: `{scheduled_id}`_")

    # Section 1: Run Summary
    lines.extend([
        "",
        "---",
        "## 1. 运行摘要",
        "",
        f"- **运行时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **触发方式:** {'DRY RUN' if dry_run else f'`{scheduled_id}`' if scheduled_id != 'manual' else '手动'}",
        f"- **执行 Work Orders:** {len(results)}",
        f"- ✅ 成功: {completed}",
        f"- ❌ 失败: {failed}",
        f"- 🔍 Needs Review: {needs_review}",
    ])

    # Section 2: Runtime Health
    lines.extend([
        "",
        "---",
        "## 2. Runtime Health",
        "",
    ])
    if all_healthy:
        lines.append("> ✅ 所有 Runtime 正常运行\n")
    else:
        lines.append(f"> ⚠️ 以下 Runtime 异常: **{', '.join(any_unhealthy)}**\n")
    lines.append(_health_table(health_results))

    # Section 3: Work Orders
    lines.extend([
        "",
        "---",
        "## 3. Work Orders",
        "",
    ])
    if not results:
        lines.append("_本次运行未创建 Work Orders。_")
    else:
        for i, result in enumerate(results, 1):
            lines.append("")
            lines.append(_format_run_result(result))

    # Section 4: Cost
    lines.extend([
        "",
        "---",
        "## 4. Cost Summary",
        "",
        _cost_section(cost_summary),
    ])

    # Section 5: Budget / Failure Warnings
    lines.extend([
        "",
        "---",
        "## 5. Budget & Failure Warnings",
        "",
    ])
    if not budget_warnings and not failures:
        lines.append("_无警告。_")
    if budget_warnings:
        lines.append("### Budget Warnings")
        for w in budget_warnings:
            lines.append(f"- ⚠️ {w}")
    if failures:
        lines.append("### Failure Details")
        for f in failures:
            lines.append(f"- {f.get('message', str(f)[:200])}")

    # Section 6: Important Findings
    lines.extend([
        "",
        "---",
        "## 6. 重要发现",
        "",
        "_由 Agent 执行结果决定。_",
    ])
    # Collect agent summaries
    for result in results:
        summary = (result.get("execution_result", {})
                   .get("summary", "")
                   or result.get("work_order", {}).get("result_summary", ""))
        if summary:
            lines.append(f"- {summary[:500]}")

    # Section 7: Founder Decisions
    lines.extend([
        "",
        "---",
        "## 7. 需要 Founder 决策的事项",
        "",
    ])
    # Auto-detect items needing founder attention
    founder_items = []
    if any_unhealthy:
        founder_items.append(f"⚠️ Runtime 异常: {', '.join(any_unhealthy)} — 需要检查并修复")
    if failed > 0:
        founder_items.append(f"❌ {failed} 个 Work Order 执行失败 — 需要 review 失败原因")
    if needs_review > 0:
        founder_items.append(f"🔍 {needs_review} 个任务进入 Needs Review — 需要 Founder 逐个确认")
    if budget_warnings:
        founder_items.append(f"💰 Budget 溢出 — 需要决定是否放宽阈值或暂停对应任务")

    if founder_items:
        for item in founder_items:
            lines.append(f"- [ ] {item}")
    else:
        lines.append("_本次无需要 Founder 决策的事项。_")

    # Section 8: Next Steps
    lines.extend([
        "",
        "---",
        "## 8. 下一步建议",
        "",
        "- 查看失败 Work Orders 的详细日志",
        "- 如有 Budget Warning，调整 budget_policy.yaml 阈值",
        "- 确认 CEO Brief 质量后再将 Operating Loop 接入 launchd",
    ])

    # Footer metadata
    lines.extend([
        "",
        "---",
        f"_Generated by AI Company OS v0.17 Operating Loop at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_",
        f"_{'DRY RUN — no execution' if dry_run else f'{len(results)} Work Order(s) executed'}_",
    ])

    return "\n".join(lines)


def save_brief(content: str, brief_date: Optional[date] = None,
               dry_run: bool = False) -> str:
    """Save CEO Brief to reports/ceo-briefs/YYYY-MM-DD.md.

    Args:
        content: Markdown content.
        brief_date: Date for the filename (default: today).
        dry_run: If True, prepend filename with 'DRY-RUN-'.

    Returns:
        Absolute path to the saved file.
    """
    if brief_date is None:
        brief_date = date.today()
    _ensure_reports_dir()

    prefix = "DRY-RUN-" if dry_run else ""
    filename = f"{prefix}{brief_date.isoformat()}.md"
    path = os.path.join(_REPORTS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[ceo_brief] 💼 CEO Brief saved → {path}")
    return path
