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
        "runtime_id": "codex",
        "runtime_type": "codex",
        "display_name": "Codex CLI",
        "adapter_module": "app.runtime.code_capable.codex_adapter",
        "endpoint": None,
        "enabled": 1,   # v0.9: A0 verified, codex exec available
        # Falls back to mock adapter if codex exec is unavailable at runtime
    },
    {
        "runtime_id": "claude-code",
        "runtime_type": "claude_code",
        "display_name": "Claude Code (Experimental)",
        "adapter_module": "app.runtime.code_capable.claude_adapter",
        "endpoint": None,
        "enabled": 0,  # v0.9: experimental, -p mode unreliable; adapter shape only
    },
    # ── Cloud runtimes (disabled; require external key) ──────────────────────
    {
        "runtime_id": "cloud-openclaw",
        "runtime_type": "openclaw",
        "display_name": "OpenClaw (Cloud)",
        "adapter_module": "app.runtime.adapters.external_http_adapter",
        "endpoint": "https://openclaw.example.com",
        "enabled": 0,
    },
    {
        "runtime_id": "cloud-hermes",
        "runtime_type": "hermes",
        "display_name": "Hermes (Cloud)",
        "adapter_module": "app.runtime.adapters.external_http_adapter",
        "endpoint": "https://hermes.example.com",
        "enabled": 0,
    },
    {
        "runtime_id": "minimax-agent",
        "runtime_type": "cloud_agent",
        "display_name": "MiniMax Agent",
        "adapter_module": "app.runtime.adapters.external_http_adapter",
        "endpoint": "https://api.minimax.example.com/agent",
        "enabled": 0,
    },
]


def seed_runtimes():
    """Insert or update default runtimes.

    Safe to call on every startup — uses INSERT OR REPLACE for idempotent updates,
    so changes to enabled/adapter_module/etc are picked up on restart.
    Also cleans up legacy stub records from v0.6.
    """
    from app.database import sync_engine
    from sqlalchemy import text

    with sync_engine.connect() as conn:
        # Clean up legacy stub records (v0.6 placeholder naming)
        conn.execute(
            text("DELETE FROM runtime_registry WHERE runtime_id IN ('codex-stub', 'claude-code-stub')")
        )

        for r in DEFAULT_RUNTIMES:
            conn.execute(
                text("""
                    INSERT OR REPLACE INTO runtime_registry
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

    print(f"[runtime/seed] Seeded {len(DEFAULT_RUNTIMES)} default runtimes (INSERT OR REPLACE)")
