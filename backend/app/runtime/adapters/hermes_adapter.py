# @PRODUCT Adapter — OS Core
import subprocess
import re
import time
from typing import Optional
from app.runtime.base_adapter import BaseRuntimeAdapter
from app.runtime.protocol import RuntimeStatus


class LocalHermesAdapter(BaseRuntimeAdapter):
    """Adapter for local Hermes Agent CLI."""

    @property
    def runtime_type(self) -> str:
        return "hermes"

    async def health_check(self) -> RuntimeStatus:
        """Run hermes status and parse output."""
        start = time.monotonic()
        try:
            result = subprocess.run(
                ["hermes", "status"],
                capture_output=True, text=True, timeout=15,
            )
            latency = int((time.monotonic() - start) * 1000)
            self._latency_ms = latency

            if result.returncode != 0:
                return RuntimeStatus.DEGRADED

            # Check for key indicators in output
            output = result.stdout + result.stderr
            if "Environment" in output and "Model:" in output:
                return RuntimeStatus.ONLINE
            return RuntimeStatus.DEGRADED

        except subprocess.TimeoutExpired:
            return RuntimeStatus.OFFLINE
        except FileNotFoundError:
            return RuntimeStatus.OFFLINE
        except Exception:
            return RuntimeStatus.UNKNOWN

    async def get_capabilities(self) -> list[dict]:
        try:
            result = subprocess.run(
                ["hermes", "status"],
                capture_output=True, text=True, timeout=15,
            )
            # Parse capabilities from skills list
            skills_count = 0
            for line in result.stdout.split("\n"):
                if "skills" in line.lower():
                    match = re.search(r"skills.*?(\d+)", line, re.IGNORECASE)
                    if match:
                        skills_count = int(match.group(1))

            caps = [
                {"name": "conversation", "type": "chat",
                 "description": "对话交互与工具调用", "enabled": True},
                {"name": "tool_use", "type": "execution",
                 "description": f"{skills_count or 30}+ 工具调用", "enabled": True},
                {"name": "skill_loading", "type": "extensibility",
                 "description": f"Skills 加载 ({skills_count or 80}+)", "enabled": True},
                {"name": "memory", "type": "knowledge",
                 "description": "会话搜索与记忆", "enabled": True},
                {"name": "multi_provider", "type": "flexibility",
                 "description": "多 Model/Provider 支持", "enabled": True},
            ]
            return caps
        except Exception:
            return []

    @property
    def latency_ms(self) -> int:
        return getattr(self, "_latency_ms", 0)


def create_adapter(reg: dict):
    """Factory function for dynamic import."""
    return LocalHermesAdapter(
        runtime_id=reg["runtime_id"],
        display_name=reg["display_name"],
        endpoint=reg.get("endpoint"),
    )
