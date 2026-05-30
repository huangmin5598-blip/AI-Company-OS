"""v0.17.1 — Canonical project configuration.

Single source of truth for:
  - PROJECT_ROOT: absolute path to the project root
  - BACKEND_ROOT: absolute path to backend/
  - DATABASE_PATH: absolute path to SQLite DB
  - DATABASE_URL: SQLAlchemy connection string

All components (API / worker / operating loop / scripts / tests)
MUST import from here instead of constructing relative paths.

Env override: AI_COMPANY_OS_DATABASE_PATH for custom DB location.
"""

import os

# ── Absolute path anchors ──

_CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))       # backend/app/
BACKEND_ROOT = os.path.abspath(os.path.join(_CONFIG_DIR, ".."))  # backend/
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_ROOT, "..")) # project root

# ── Database path ──
# Default: backend/data/ai_company_os.db
# Override with AI_COMPANY_OS_DATABASE_PATH env var

_DEFAULT_DB_DIR = os.path.join(BACKEND_ROOT, "data")
_DEFAULT_DB_PATH = os.path.join(_DEFAULT_DB_DIR, "ai_company_os.db")

DATABASE_PATH = os.environ.get("AI_COMPANY_OS_DATABASE_PATH") or _DEFAULT_DB_PATH
DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH}"

# Ensure data directory exists (idempotent)
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)


class Settings:
    DATABASE_URL: str = DATABASE_URL


settings = Settings()
