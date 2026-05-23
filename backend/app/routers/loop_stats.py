# @PRODUCT Router — OS Core
from fastapi import APIRouter
from datetime import datetime, timedelta
from app.database import get_sync_session
from app.models.task_pool import TaskPool
from app.models.approval import Approval
from app.models.review import Review
from app.models.learning_candidate import LearningCandidate
from app.schemas.loop_stats import LoopStatsResponse

router = APIRouter(tags=["Loop Stats"])


@router.get("/api/v1/loop-stats", response_model=LoopStatsResponse)
def get_loop_stats():
    session = get_sync_session()
    try:
        # Total tasks
        total_tasks = session.query(TaskPool).count()

        # Alert-pooled count
        alert_pooled_count = session.query(TaskPool).filter(
            TaskPool.source == "alert"
        ).count()

        # Approval rate
        total_approvals = session.query(Approval).count()
        approved_count = session.query(Approval).filter(
            Approval.status == "approved"
        ).count()
        approval_rate = (approved_count / total_approvals * 100) if total_approvals > 0 else 0.0

        # Review distribution
        all_reviews = session.query(Review).all()
        review_distribution = {}
        for r in all_reviews:
            review_distribution[r.result] = review_distribution.get(r.result, 0) + 1

        # Learning candidates
        candidate_count = session.query(LearningCandidate).count()
        candidate_approved_count = session.query(LearningCandidate).filter(
            LearningCandidate.approval_status.in_(["approved", "approved_for_knowledge_update"])
        ).count()

        # Pending approval tasks (status = approval_required)
        pending_approval_tasks = session.query(TaskPool).filter(
            TaskPool.status == "approval_required"
        ).count()

        # Pending candidates
        pending_candidates = session.query(LearningCandidate).filter(
            LearningCandidate.approval_status == "pending_approval"
        ).count()

        # Recent task trend (last 7 days)
        recent_task_trend = []
        today = datetime.utcnow()
        for i in range(6, -1, -1):
            day_start = today - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            count = session.query(TaskPool).filter(
                TaskPool.created_at >= day_start,
                TaskPool.created_at < day_end,
            ).count()
            recent_task_trend.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "count": count,
            })

        return LoopStatsResponse(
            total_tasks=total_tasks,
            alert_pooled_count=alert_pooled_count,
            approval_rate=round(approval_rate, 1),
            review_distribution=review_distribution,
            candidate_count=candidate_count,
            candidate_approved_count=candidate_approved_count,
            pending_approval_tasks=pending_approval_tasks,
            pending_candidates=pending_candidates,
            recent_task_trend=recent_task_trend,
        )
    finally:
        session.close()
