# @PRODUCT Runtime seed — OS Core
"""Seed default runtimes into the registry. Idempotent — safe to call on every startup."""

from app.database import get_sync_session
from app.models.runtime_registry import RuntimeRegistry


DEFAULT_RUNTIMES = [
    {
        "runtime_id": "hermes-local",
        "runtime_type": "hermes",
        "display_name": "Hermes Agent",
        "adapter_module": "app.runtime.adapters.hermes_adapter",
        "endpoint": None,
        "enabled": 1,
    },
    {
        "runtime_id": "openclaw-local",
        "runtime_type": "openclaw",
        "display_name": "OpenClaw Gateway",
        "adapter_module": "app.runtime.adapters.openclaw_adapter",
        "endpoint": "http://localhost:18789",
        "enabled": 1,
    },
    {
        "runtime_id": "codex-stub",
        "runtime_type": "codex",
        "display_name": "Codex",
        "adapter_module": "app.runtime.adapters.codex_stub",
        "endpoint": None,
        "enabled": 0,  # Placeholder — not ready; suppressed from Monitor noise
    },
    {
        "runtime_id": "claude-code-stub",
        "runtime_type": "claude_code",
        "display_name": "Claude Code",
        "adapter_module": "app.runtime.adapters.claude_code_stub",
        "endpoint": None,
        "enabled": 0,  # Placeholder — not ready; suppressed from Monitor noise
    },
]


def seed_runtimes():
    """Insert default runtimes with INSERT OR IGNORE for idempotency.

    Safe to call on every startup — duplicates are silently skipped.
    """
    from app.database import sync_engine
    from sqlalchemy import text

    with sync_engine.connect() as conn:
        for r in DEFAULT_RUNTIMES:
            conn.execute(
                text("""
                    INSERT OR IGNORE INTO runtime_registry
                        (runtime_id, runtime_type, display_name, adapter_module, endpoint, enabled)
                    VALUES
                        (:runtime_id, :runtime_type, :display_name, :adapter_module, :endpoint, :enabled)
                """),
                {
                    "runtime_id": r["runtime_id"],
                    "runtime_type": r["runtime_type"],
                    "display_name": r["display_name"],
                    "adapter_module": r["adapter_module"],
                    "endpoint": r["endpoint"],
                    "enabled": r["enabled"],
                },
            )
        conn.commit()

    print(f"[runtime/seed] Seeded {len(DEFAULT_RUNTIMES)} default runtimes (INSERT OR IGNORE)")
