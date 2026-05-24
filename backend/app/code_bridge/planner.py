# @PRODUCT Code Bridge — v0.9
"""Plan generator — calls Code-Capable Runtime to generate a natural language plan."""
from typing import Optional
from app.runtime.code_capable import PlanResult
from app.runtime.code_capable.factory import get_code_runtime


class CodePlanner:
    def __init__(self, runtime_type: str = "codex"):
        self.runtime_type = runtime_type

    async def generate(self, problem: str, workdir: str) -> PlanResult:
        adapter = get_code_runtime(self.runtime_type)
        if adapter is None:
            raise RuntimeError(f"Code-Capable Runtime '{self.runtime_type}' is not available")
        context = {"workdir": workdir}
        return await adapter.generate_plan(problem, context)
