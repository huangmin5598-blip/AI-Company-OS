# @PRODUCT Adapter — OS Core (placeholder)
from app.runtime.base_adapter import BaseRuntimeAdapter
from app.runtime.protocol import RuntimeStatus


class CodexAdapterStub(BaseRuntimeAdapter):
    """Placeholder for future Codex integration."""

    @property
    def runtime_type(self) -> str:
        return "codex"

    async def health_check(self) -> RuntimeStatus:
        return RuntimeStatus.OFFLINE

    async def get_capabilities(self) -> list[dict]:
        return [
            {"name": "code_generation", "type": "code",
             "description": "代码生成（未接入）", "enabled": False},
            {"name": "code_review", "type": "quality",
             "description": "代码审查（未接入）", "enabled": False},
            {"name": "pr_management", "type": "workflow",
             "description": "Pull Request 管理（未接入）", "enabled": False},
        ]


def create_adapter(reg: dict):
    return CodexAdapterStub(reg["runtime_id"], reg["display_name"])
