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

routers = [
    stats_router, agents_router, business_lines_router, runs_router,
    artifacts_router, costs_router, cron_jobs_router, alerts_router, refresh_router,
    tasks_router, commands_router, analysis_router,
]
