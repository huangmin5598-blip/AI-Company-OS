# @PRODUCT Database setup — OS Core
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session
from app.config import settings
from app.models.base import Base
import os

os.makedirs("data", exist_ok=True)

# Async engine for FastAPI
async_engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session_factory = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# Sync engine for seed/scripts
sync_engine = create_engine(settings.DATABASE_URL.replace("+aiosqlite", ""), echo=False)

def init_db():
    """Create all tables and initialize FTS5."""
    Base.metadata.create_all(bind=sync_engine)
    # FTS5 virtual table + triggers (graceful fallback if unavailable)
    from app.models.fts_triggers import init_fts5
    init_fts5()

def get_sync_session() -> Session:
    return Session(bind=sync_engine)


def upgrade_schema_v012():
    """Add new columns introduced in v0.12 (scope, current_goal, etc.) to existing tables.

    SQLite doesn't support ALTER TABLE ADD COLUMN IF NOT EXISTS, so we check existence
    by querying PRAGMA table_info. Idempotent — safe to call on every startup.
    """
    with sync_engine.connect() as conn:
        # Check which columns exist in product_line_registry
        existing = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(product_line_registry)")).fetchall()
        }
        v0_12_cols = {
            "scope": "TEXT DEFAULT ''",
            "current_goal": "TEXT DEFAULT ''",
            "active_projects": "TEXT DEFAULT ''",
            "weekly_status": "TEXT DEFAULT ''",
        }
        for col_name, col_def in v0_12_cols.items():
            if col_name not in existing:
                conn.execute(text(f"ALTER TABLE product_line_registry ADD COLUMN {col_name} {col_def}"))
                print(f"[upgrade_schema_v012] Added column: {col_name}")
        conn.commit()
    print("[upgrade_schema_v012] Schema check complete")

async def get_async_session():
    async with async_session_factory() as session:
        yield session
