# @PRODUCT Base RuntimeAdapter — OS Core
from typing import Any, Optional
from app.runtime.protocol import RuntimeStatus


class BaseRuntimeAdapter:
    """Base class for runtime adapters. Subclasses override glue methods.

    v0.6 is a read-only status layer, NOT an execution layer.
    create_session / execute / cancel_session / get_cost raise RuntimeError
    — even if the runtime natively supports execution.
    """

    def __init__(self, runtime_id: str, display_name: str, endpoint: Optional[str] = None):
        self._runtime_id = runtime_id
        self._display_name = display_name
        self._endpoint = endpoint

    @property
    def runtime_id(self) -> str:
        return self._runtime_id

    @property
    def name(self) -> str:
        return self._display_name

    @property
    def runtime_type(self) -> str:
        raise NotImplementedError

    async def health_check(self) -> RuntimeStatus:
        raise NotImplementedError

    async def get_capabilities(self) -> list[dict]:
        raise NotImplementedError

    async def create_session(self, goal: str, context: Optional[dict] = None):
        raise RuntimeError(f"{self.name} does not support session creation in v0.6")

    async def execute(self, session, command: str, timeout: int = 300):
        raise RuntimeError(f"{self.name} does not support execution in v0.6")

    async def cancel_session(self, session_id: str):
        raise RuntimeError(f"{self.name} does not support session cancellation in v0.6")

    async def get_cost(self, session_id: str):
        raise RuntimeError(f"{self.name} does not support cost tracking in v0.6")
