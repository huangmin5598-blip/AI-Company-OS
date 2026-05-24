# AI Company Control Center v0.9 — Code-Capable Runtime Bridge MVP Execution Plan

> **状态**: 📋 执行计划 · 待执行
> **Sprint**: A0 (1h) → A (3.5h) → B (4.5h) → C (2.5h) ≈ 11-13h

---

## Sprint A0 (~1h) — Code Runtime Capability Spike

**目标**: 确认 Codex / Claude Code CLI 是否为可用、非交互生成 plan/patch、workspace 限制。根据结果决定启用状态，不可用时升级 mock 不阻塞。

| # | 操作 | 验证目标 | 预期产出 |
|:-:|:-----|:---------|:---------|
| 1 | `codex --version` / `codex --help` | CLI 是否安装 | version / help |
| 2 | `codex -q "..."` 非交互 | plan 能否非交互输出 | plan text stdout |
| 3 | 限制 workspace | 能否指定工作目录 | 文件生成在指定目录 |
| 4 | patch 输出格式 | 能否输出 diff | patch.diff |
| 5 | `claude --version` / `claude --help` | CLI 是否安装 | version / help |
| 6 | 决策 | enabled=1 vs experimental | 写入执行计划 |

**降级路径**: 如果 Codex 不可用，定义 MockCodexAdapter 返回预设 plan/patch，后端结构不受影响。

---

## Sprint A (~3.5h) — Code-Capable Runtime 抽象 + Codex Adapter

```python
# 目标接口 (backend/app/runtime/code_capable/base.py)
class CodeCapableAdapter(ABC):
    runtime_type: str

    @abstractmethod
    async def generate_plan(self, problem: str, context: dict) -> PlanResult:
        """分析代码 → plan_summary + impact_scope"""

    @abstractmethod
    async def generate_patch(self, plan: dict, workspace: str) -> PatchResult:
        """生成 patch 到指定目录"""

    @abstractmethod
    async def run_checks(self, check_workspace: str) -> CheckResult:
        """在 isolated workspace 运行 build/lint"""

    @abstractmethod
    async def health_check(self) -> HealthResult:
        """Runtime 是否可用"""
```

| Step | 文件 | 说明 |
|:-----|:-----|:------|
| 1 | `backend/app/runtime/code_capable/__init__.py` | 包 init + 工厂函数 |
| 2 | `backend/app/runtime/code_capable/base.py` | CodeCapableAdapter ABC + PlanResult/PatchResult/CheckResult/HealthResult dataclass |
| 3 | `backend/app/runtime/code_capable/codex_adapter.py` | Codex CLI 真实调用（或 mock 降级） |
| 4 | `backend/app/runtime/code_capable/claude_adapter.py` | Claude Code shape（health + capability，不跑完整流程） |
| 5 | `backend/app/runtime/code_capable/mock_adapter.py` | Mock adapter（A0 验证不可用时兜底） |
| 6 | `backend/app/runtime/routes.py` | 扩展 capability discovery |
| 7 | `backend/app/models/runtime_registry.py` | seed 更新 |

### 验证

- ✅ Codex adapter health check 正常
- ✅ Capability discovery 返回 `["code_plan", "code_patch", "code_check"]`
- ✅ Mock adapter 可完整执行 plan/patch/check

---

## Sprint B (~4.5h) — code_change_requests 表 + 后端链路

| Step | 文件 | 说明 |
|:-----|:-----|:------|
| 8 | `backend/app/models/code_change_request.py` | 模型定义 |
| 9 | `backend/app/models/__init__.py` | 注册模型 |
| 10 | `backend/app/routers/code_change_requests.py` | CRUD + 状态机路由（8 种状态） |
| 11 | `backend/app/code_bridge/__init__.py` | 包初始化 |
| 12 | `backend/app/code_bridge/planner.py` | Plan 生成逻辑 |
| 13 | `backend/app/code_bridge/patch_generator.py` | Patch 生成 + original_files + check_workspace + modified_files |
| 14 | `backend/app/code_bridge/checks_runner.py` | 在 check_workspace 中运行 build/lint/import |
| 15 | `backend/app/code_bridge/protected_files.py` | Pre-check + Post-check 双层策略 |
| 16 | `backend/app/code_bridge/applier.py` | Apply + Path safety + Rollback |
| 17 | `backend/app/routers/execution_requests.py` | 扩展 action_type=code_change_request |
| 18 | `backend/app/execution_bridge/policy.py` | modify_code 从 blocked 移到 v0.9 |

### 后端 API 端点

```
GET    /api/v1/code-change-requests
GET    /api/v1/code-change-requests/{id}
POST   /api/v1/code-change-requests/{id}/generate-plan
POST   /api/v1/code-change-requests/{id}/approve-plan
POST   /api/v1/code-change-requests/{id}/generate-patch
POST   /api/v1/code-change-requests/{id}/run-checks
POST   /api/v1/code-change-requests/{id}/apply
POST   /api/v1/code-change-requests/{id}/rollback
POST   /api/v1/code-change-requests/{id}/reject
POST   /api/v1/code-change-requests/{id}/revise
```

### 验证

- ✅ Plan → Approve → Patch → Checks → Apply → Rollback 全链路
- ✅ Protected files post-check 阻止违规 apply
- ✅ Path traversal 被拒绝
- ✅ Apply → verification_pending（不直接 closed_success）

---

## Sprint C (~2.5h) — 前端 + 收尾

| Step | 文件 | 说明 |
|:-----|:-----|:------|
| 20 | `frontend/src/types/code_change.ts` | TypeScript 类型 |
| 21 | `frontend/src/lib/api.ts` | API 函数 |
| 22 | `frontend/src/app/code-change-requests/page.tsx` | 列表页 |
| 23 | `frontend/src/app/code-change-requests/[id]/page.tsx` | 详情页（摘要、checks_warning 二次确认、verification_pending） |
| 24 | `frontend/src/app/layout.tsx` | 导航链接 |
| 25 | 验证 | 验收 1-12 |
| 26 | Commit + Tag + Release | v0.9 |
