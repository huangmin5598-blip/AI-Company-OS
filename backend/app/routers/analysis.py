"""Analysis API — failure clustering + skill gap recommendations."""
from fastapi import APIRouter
from collections import Counter, defaultdict
from app.database import get_sync_session
from app.models.task import Task, TaskMessage
from app.models.agent import Agent

router = APIRouter(tags=["Analysis"])


@router.get("/api/v1/analysis/failures")
def get_failure_analysis():
    """Return failure clustering — by reason, by agent, by skill."""
    session = get_sync_session()
    try:
        failed_tasks = session.query(Task).filter(Task.status == "failed").all()

        # By failure_reason
        reason_counter: Counter[str] = Counter()
        # By agent
        agent_counter: Counter[str] = Counter()
        # By skill
        skill_counter: Counter[str] = Counter()
        # Time series
        daily_failures: Counter[str] = Counter()

        failures_detail = []
        for t in failed_tasks:
            reason = t.failure_reason or "unknown"
            reason_counter[reason] += 1
            agent_counter[t.agent_id] += 1
            if t.created_at:
                date_key = t.created_at.isoformat()[:10] if hasattr(t.created_at, 'isoformat') else str(t.created_at)[:10]
                daily_failures[date_key] += 1
            else:
                daily_failures["unknown"] += 1

            # Extract skills from required_skills
            if t.required_skills:
                try:
                    import json
                    skills = json.loads(t.required_skills)
                    for s in skills:
                        skill_counter[s.lower().strip()] += 1
                except (json.JSONDecodeError, TypeError):
                    pass

            failures_detail.append({
                "task_id": t.id,
                "title": t.title[:60],
                "agent_id": t.agent_id,
                "failure_reason": reason,
                "error_message": t.error_message[:100] if t.error_message else None,
                "created_at": str(t.created_at) if t.created_at else None,
            })

        # Build recommendations
        recommendations = []

        # 1. Top failure reasons
        top_reasons = reason_counter.most_common(5)
        for reason, count in top_reasons:
            if count >= 2:
                recommendations.append({
                    "type": "high_frequency_failure",
                    "reason": reason,
                    "count": count,
                    "suggestion": f"'{reason}' 已失败 {count} 次，建议检查相关 Agent 配置或 API 权限",
                })

        # 2. Agents with high failure rates
        all_tasks = session.query(Task).all()
        agent_total: Counter[str] = Counter()
        for t in all_tasks:
            agent_total[t.agent_id] += 1

        for agent, fails in agent_counter.most_common(5):
            total = agent_total.get(agent, 1)
            fail_rate = fails / total * 100
            if fail_rate > 30 and fails >= 2:
                recommendations.append({
                    "type": "high_failure_agent",
                    "agent": agent,
                    "fail_count": fails,
                    "total_tasks": total,
                    "fail_rate": round(fail_rate, 1),
                    "suggestion": f"Agent '{agent}' 失败率 {fail_rate:.0f}%（{fails}/{total}），建议检查 Agent 配置或分配的任务类型",
                })

        return {
            "total_failed": len(failed_tasks),
            "total_tasks": len(all_tasks),
            "failure_rate": round(len(failed_tasks) / max(len(all_tasks), 1) * 100, 1),
            "by_reason": [{"reason": r, "count": c} for r, c in reason_counter.most_common()],
            "by_agent": [{"agent": a, "count": c} for a, c in agent_counter.most_common()],
            "by_skill": [{"skill": s, "count": c} for s, c in skill_counter.most_common()],
            "daily": [{"date": d, "count": c} for d, c in sorted(daily_failures.items())],
            "recent_failures": failures_detail[-10:][::-1],
            "recommendations": recommendations[:5],
        }
    finally:
        session.close()


@router.get("/api/v1/analysis/gaps")
def get_gap_recommendations():
    """Analyze skill gaps and recommend new agent types."""
    session = get_sync_session()
    try:
        # Get all tasks with required skills
        all_tasks = session.query(Task).all()

        # Get all agents with skills
        agents = session.query(Agent).all()
        existing_skills: set[str] = set()
        for a in agents:
            if a.skills:
                try:
                    import json
                    existing_skills.update(json.loads(a.skills))
                except (json.JSONDecodeError, TypeError):
                    pass

        # Find gap skills that appear repeatedly
        gap_counter: Counter[str] = Counter()
        gap_tasks: dict[str, list[dict]] = defaultdict(list)

        for t in all_tasks:
            if t.required_skills:
                try:
                    import json
                    req_skills = json.loads(t.required_skills)
                except (json.JSONDecodeError, TypeError):
                    req_skills = []
                for rs in req_skills:
                    rs_lower = rs.lower().strip()
                    if rs_lower not in {s.lower().strip() for s in existing_skills}:
                        gap_counter[rs_lower] += 1
                        gap_tasks[rs_lower].append({
                            "task_id": t.id,
                            "title": t.title[:60],
                            "status": t.status,
                        })

        # Build recommendations
        recommendations = []
        for skill, count in gap_counter.most_common():
            if count >= 2:
                severity = "high" if count >= 4 else ("medium" if count >= 2 else "low")
                recommendations.append({
                    "skill": skill,
                    "occurrence_count": count,
                    "severity": severity,
                    "related_tasks": gap_tasks[skill][:5],
                    "suggestion": (
                        f"技能 '{skill}' 缺失，已在 {count} 个任务中需要。"
                        + (" 建议考虑创建具备此技能的 Agent。" if severity == "high" else "")
                    ),
                })

        return {
            "total_gap_skills": len(gap_counter),
            "recommendations": recommendations[:10],
            "gap_details": [{"skill": s, "count": c, "tasks": gap_tasks[s][:3]} for s, c in gap_counter.most_common()],
        }
    finally:
        session.close()
