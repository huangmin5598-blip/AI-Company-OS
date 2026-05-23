from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import create_engine, event
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

async def get_async_session():
    async with async_session_factory() as session:
        yield session
