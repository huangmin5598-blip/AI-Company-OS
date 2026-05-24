from app.routers.stats import router as stats_router
from app.routers.agents import router as agents_router
from app.routers.business_lines import router as business_lines_router
from app.routers.runs import router as runs_router
from app.routers.artifacts import router as artifacts_router
from app.routers.costs import router as costs_router
from app.routers.cron_jobs import router as cron_jobs_router
from app.routers.alerts import router as alerts_router
from app.routers.refresh import router as refresh_router
from app.routers.tasks import router as tasks_router
from app.routers.commands import router as commands_router
from app.routers.analysis import router as analysis_router
from app.routers.monitor import router as monitor_router
from app.routers.chat import router as chat_router
from app.routers.task_pool import router as task_pool_router
from app.routers.context_packs import router as context_packs_router
from app.routers.approvals import router as approvals_router
from app.routers.reviews import router as reviews_router
from app.routers.learning_candidates import router as learning_candidates_router
from app.routers.loop_stats import router as loop_stats_router
from app.routers.alert_to_task import router as alert_to_task_router
from app.routers.goal_sessions import router as goal_sessions_router
from app.routers.ceo_action_logs import router as ceo_action_logs_router
from app.routers.ceo_commit import router as ceo_commit_router
from app.routers.memory_entries import router as memory_entries_router
from app.routers.memory_search import router as memory_search_router
from app.routers.memory_recall import router as memory_recall_router
from app.routers.memory_proposals import router as memory_proposals_router
from app.routers.memory_from_candidate import router as memory_from_candidate_router
from app.routers.monitor_runs import router as monitor_runs_router
from app.routers.runtime_registry import router as runtime_registry_router
from app.routers.improvement_proposals import router as improvement_proposals_router
from app.routers.execution_requests import router as execution_requests_router

routers = [
    stats_router, agents_router, business_lines_router, runs_router,
    artifacts_router, costs_router, cron_jobs_router, alerts_router, refresh_router,
    tasks_router, commands_router, analysis_router, monitor_router, chat_router,
    task_pool_router, context_packs_router, approvals_router, reviews_router,
    learning_candidates_router, loop_stats_router, alert_to_task_router,
    goal_sessions_router, ceo_action_logs_router, ceo_commit_router,
    memory_entries_router, memory_search_router, memory_recall_router,
    memory_proposals_router, memory_from_candidate_router,
    monitor_runs_router,
    runtime_registry_router,
    improvement_proposals_router,
    execution_requests_router,
]
