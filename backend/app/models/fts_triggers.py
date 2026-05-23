# @PRODUCT Model — OS Core
"""FTS5 virtual table + LIKE fallback for OrgMemory search.

Capability check on startup: if SQLite supports FTS5, create virtual table + sync triggers.
Otherwise, all search/recall endpoints fall back to LIKE queries — system never crashes."""
import logging
import sqlite3
from sqlalchemy import text
from app.database import sync_engine

logger = logging.getLogger(__name__)

FTS5_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS org_memory_fts USING fts5(
  title, summary, content, tags,
  content='org_memory',
  content_rowid='id'
);
"""

FTS5_TRIGGERS_SQL = [
    """
    CREATE TRIGGER IF NOT EXISTS org_memory_ai AFTER INSERT ON org_memory BEGIN
      INSERT INTO org_memory_fts(rowid, title, summary, content, tags)
      VALUES (new.id, new.title, new.summary, new.content, new.tags);
    END;
    """,
    """
    CREATE TRIGGER IF NOT EXISTS org_memory_ad AFTER DELETE ON org_memory BEGIN
      INSERT INTO org_memory_fts(org_memory_fts, rowid, title, summary, content, tags)
      VALUES ('delete', old.id, old.title, old.summary, old.content, old.tags);
    END;
    """,
    """
    CREATE TRIGGER IF NOT EXISTS org_memory_au AFTER UPDATE ON org_memory BEGIN
      INSERT INTO org_memory_fts(org_memory_fts, rowid, title, summary, content, tags)
      VALUES ('delete', old.id, old.title, old.summary, old.content, old.tags);
      INSERT INTO org_memory_fts(rowid, title, summary, content, tags)
      VALUES (new.id, new.title, new.summary, new.content, new.tags);
    END;
    """,
]


def fts5_available() -> bool:
    """Detect whether the current SQLite build supports FTS5."""
    try:
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS test_fts USING fts5(content)")
        conn.close()
        return True
    except Exception:
        return False


def init_fts5() -> None:
    """Initialize FTS5 virtual table and triggers if available."""
    if not fts5_available():
        logger.warning("[FTS5] Not available — search/recall will use LIKE fallback. System will not crash.")
        return

    try:
        with sync_engine.connect() as conn:
            conn.execute(text(FTS5_SQL))
            for trigger_sql in FTS5_TRIGGERS_SQL:
                conn.execute(text(trigger_sql))
            conn.commit()
        logger.info("[FTS5] Virtual table + triggers initialized successfully.")
    except Exception as e:
        logger.error(f"[FTS5] Init failed: {e} — falling back to LIKE search.")
