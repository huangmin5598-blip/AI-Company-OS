# @PRODUCT Adapter — OS Core
import json
import time
import re
import subprocess
import os
from typing import Optional
import httpx
from app.runtime.base_adapter import BaseRuntimeAdapter
from app.runtime.protocol import RuntimeStatus


class LocalOpenClawAdapter(BaseRuntimeAdapter):
    """Adapter for local OpenClaw Gateway."""

    def __init__(self, runtime_id: str, display_name: str, endpoint: str = "http://localhost:18789"):
        super().__init__(runtime_id, display_name, endpoint)
        self._health_url = f"{endpoint}/health"
        self._dashboard_url = endpoint

    @property
    def runtime_type(self) -> str:
        return "openclaw"

    async def health_check(self) -> RuntimeStatus:
        try:
            start = time.monotonic()
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(self._health_url)
            latency = int((time.monotonic() - start) * 1000)
            self._latency_ms = latency

            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok") and data.get("status") == "live":
                    return RuntimeStatus.ONLINE
                return RuntimeStatus.DEGRADED
            return RuntimeStatus.DEGRADED

        except httpx.ConnectError:
            return RuntimeStatus.OFFLINE
        except httpx.TimeoutException:
            return RuntimeStatus.OFFLINE
        except Exception:
            return RuntimeStatus.UNKNOWN

    async def get_capabilities(self) -> list[dict]:
        """Discover capabilities via openclaw CLI first, directory scan as fallback."""
        agent_names = []
        agent_count = 0

        # Primary: openclaw status CLI for total count
        try:
            result = subprocess.run(
                ["openclaw", "status"],
                capture_output=True, text=True, timeout=10,
            )
            for line in result.stdout.split("\n"):
                if "Agents" in line:
                    match = re.search(r"Agents\s+[│|]\s+(\d+)", line)
                    if match:
                        agent_count = int(match.group(1))
                        break
        except Exception:
            pass

        # Fallback: scan agents directory for names (more reliable than parsing CLI table)
        agents_dir = os.path.expanduser("~/.openclaw/agents")
        if os.path.isdir(agents_dir):
            agent_names = sorted([
                d for d in os.listdir(agents_dir)
                if os.path.isdir(os.path.join(agents_dir, d))
            ])
        else:
            # Try workspace subdirs as last fallback
            workspace = os.path.expanduser("~/.openclaw/workspace")
            if os.path.isdir(workspace):
                agent_names = sorted([
                    d for d in os.listdir(workspace)
                    if os.path.isdir(os.path.join(workspace, d))
                ])

        return [
            {"name": "agent_hosting", "type": "multi_agent",
             "description": f"多 Agent 运行 ({agent_count or len(agent_names)} agents)", "enabled": True,
             "agents": agent_names},
            {"name": "http_gateway", "type": "infrastructure",
             "description": "HTTP/WebSocket 接口", "enabled": True},
            {"name": "channel_integration", "type": "connectivity",
             "description": "Feishu/Telegram 等消息渠道", "enabled": True},
            {"name": "session_management", "type": "state",
             "description": "Agent 会话管理", "enabled": True},
        ]

    @property
    def latency_ms(self) -> int:
        return getattr(self, "_latency_ms", 0)


def create_adapter(reg: dict):
    """Factory function for dynamic import."""
    return LocalOpenClawAdapter(
        runtime_id=reg["runtime_id"],
        display_name=reg["display_name"],
        endpoint=reg.get("endpoint", "http://localhost:18789"),
    )
