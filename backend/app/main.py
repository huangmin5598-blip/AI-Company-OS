# @PRODUCT App entry point — OS Core
"""AI Company Control Center — FastAPI backend."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import routers
from app.database import init_db
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    os.makedirs("data", exist_ok=True)
    init_db()
    from app.database import upgrade_schema_v012
    upgrade_schema_v012()
    from app.refresh_orchestrator import seed_mock_fallback
    seed_mock_fallback()
    from app.database import upgrade_schema_v013
    upgrade_schema_v013()
    from app.database import upgrade_schema_v021
    upgrade_schema_v021()
    from app.runtime.seed_runtimes import seed_runtimes
    seed_runtimes()
    from app.services.seed_v010 import seed_skills, seed_product_lines
    seed_skills()
    seed_product_lines()
    yield
    # Shutdown
    print("[Shutdown] AI Company Control Center stopped")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in routers:
    app.include_router(router)

@app.get("/api/v1/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
