from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    APP_NAME: str = "AI Company Control Center"
    APP_VERSION: str = "0.1.0"

    DATABASE_URL: str = "sqlite+aiosqlite:///./data/ai_company_os.db"

    # OpenClaw paths (expanduser resolved)
    OPENCLAW_WORKSPACE: str = str(Path("~/.openclaw/workspace").expanduser().resolve())
    OPENCLAW_CRON_JOBS_PATH: str = str(Path("~/.openclaw/cron/jobs.json").expanduser().resolve())
    OPENCLAW_AGENTS_DIR: str = str(Path("~/.openclaw/agents").expanduser().resolve())
    GATEWAY_COST_DIR: str = str(Path("~/.openclaw/workspace-gateway-lite/cost-view").expanduser().resolve())
    GATEWAY_DAILY_DIR: str = str(Path("~/.openclaw/workspace-gateway-lite/daily").expanduser().resolve())
    SUBAGENT_RUNS_PATH: str = str(Path("~/.openclaw/subagents/runs.json").expanduser().resolve())
    PRODUCTION_LEDGER_PATH: str = str(Path("~/.openclaw/workspace/run-ledger-v1/db/production-flow-ledger.json").expanduser().resolve())
    ARTIFACT_LEDGER_PATH: str = str(Path("~/.openclaw/workspace/run-ledger-v1/db/artifact-ledger.json").expanduser().resolve())

    class Config:
        env_file = ".env"

settings = Settings()
