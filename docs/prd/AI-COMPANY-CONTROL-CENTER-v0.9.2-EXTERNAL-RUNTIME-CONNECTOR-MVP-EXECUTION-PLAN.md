# AI Company Control Center v0.9.2 — External Runtime Connector MVP Execution Plan

> **状态**: 📋 执行计划 · 待执行
> **Sprint**: S1 (2h) → S2 (1.5h) → S3 (1h) → S4 (1h) ≈ 5.5h
> **PRD**: `docs/prd/AI-COMPANY-CONTROL-CENTER-v0.9.2-EXTERNAL-RUNTIME-CONNECTOR-MVP-PRD.md`

---

## Sprint S1 (2h) — ExternalHTTPAgentAdapter 模板 + Mock 验证

**目标**: 完成通用 HTTP Agent 适配器基类，跑通 mock cloud agent 验证。

### 文件清单

| # | 操作 | 文件 | 说明 |
|:-:|:-----|:-----|:------|
| 1 | **新建** | `backend/app/runtime/adapters/external_http_adapter.py` | 通用 HTTP Agent 适配器类 |

### ExternalHTTPAgentAdapter 类设计

```python
class ExternalHTTPAgentAdapter:
    """通用外部 HTTP Agent 适配器模板。

    安全边界：
    - execute() 硬禁用远程执行（v0.9.2 锁定）
    - auth token 仅来自环境变量，不进 config
    - endpoint_url 需通过安全校验
    - enabled=false 不触达远程
    """

    def __init__(self, runtime_id: str, runtime_type: str, display_name: str,
                 endpoint_url: str, auth_type: str = "none",
                 auth_env: Optional[str] = None,        # 环境变量名，如 CLOUD_HERMES_TOKEN
                 health_path: str = "/health",
                 capabilities_path: str = "/capabilities",
                 execute_path: str = "/execute",
                 cost_path: str = "/cost",
                 enabled: bool = False,
                 risk_level: str = "medium",
                 timeout_seconds: int = 300):
        self._validate_endpoint(endpoint_url)
        ...

    def _validate_endpoint(self, url: str):
        """安全校验：只允许 http://localhost、http://127.0.0.1、https://"""
        parsed = urllib.parse.urlparse(url)
        allowed_schemes = {"http", "https"}
        forbidden_hosts = {"169.254.169.254", "0.0.0.0"}
        if parsed.scheme not in allowed_schemes:
            raise ValueError(f"Scheme '{parsed.scheme}' not allowed")
        if parsed.hostname in forbidden_hosts:
            raise ValueError(f"Host '{parsed.hostname}' not allowed")
        if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1"}:
            raise ValueError("HTTP only allowed for localhost/127.0.0.1")

    def _get_auth_header(self) -> dict:
        """从环境变量读取 auth token，不进 config"""
        if self.auth_type == "none":
            return {}
        env_val = os.environ.get(self.auth_env, "")
        if not env_val:
            return {}
        if self.auth_type == "bearer_token":
            return {"Authorization": f"Bearer {env_val}"}
        if self.auth_type == "api_key":
            return {"X-API-Key": env_val}
        return {}

    async def health_check(self) -> HealthResult:
        """GET {endpoint_url}{health_path} → 200 → ONLINE"""
        ...

    async def get_capabilities(self) -> list[RuntimeCapability]:
        """GET {endpoint_url}{capabilities_path} → 能力列表"""
        ...

    async def get_cost(self, session_id: str) -> dict:
        """GET {endpoint_url}{cost_path}/{session_id} → tokens / cost"""
        ...

    async def create_session(self, goal: str, context: dict = None) -> RuntimeSession:
        """返回 stub session（v0.9.2 不做远程 session 创建）"""
        ...

    async def execute(self, session: RuntimeSession, command: str, timeout: int = 300) -> dict:
        """硬禁用远程执行 — 始终返回 unsupported"""
        return {
            "status": "unsupported",
            "detail": "Remote execution is disabled in v0.9.2",
        }

    async def cancel_session(self, session_id: str) -> bool:
        """返回 stub"""
        return False

    async def health_check_local(self) -> HealthResult:
        """enabled=false 时调用 — 仅返回本地状态，不触达远程"""
        return HealthResult(
            online=False,       # 远程不可达
            runtime_type=self.runtime_type,
            version="0.0.0-disabled",
            capabilities=[],
            detail="Runtime is disabled — no remote check performed",
        )
```

### 验证

| # | 操作 | 预期 |
|:-:|:-----|:-----|
| 1 | 运行 `python3 -c "from app.runtime.adapters.external_http_adapter import ExternalHTTPAgentAdapter; a = ExternalHTTPAgentAdapter(...)"` | import 无报错 |
| 2 | 传 `endpoint_url="file:///etc/passwd"` | `ValueError` 抛出 |
| 3 | 传 `endpoint_url="http://169.254.169.254:80"` | `ValueError` 抛出 |
| 4 | 传 `endpoint_url="ftp://example.com"` | `ValueError` 抛出 |
| 5 | 传 `endpoint_url="https://api.example.com"` | ✅ 通过 |
| 6 | 传 `endpoint_url="http://localhost:8080"` | ✅ 通过 |
| 7 | 启动 mock HTTP server（Flask/stdlib），`health_check()` 请求 /health → 200 | 返回 ONLINE |
| 8 | `get_capabilities()` 请求 /capabilities → 能力列表 | 返回有效列表 |
| 9 | `execute()` 调用 → 始终返回 unsupported | 确认不 POST 到远程 |
| 10 | `health_check_local()` → enabled=false 不触达 | 返回 status=disabled |

---

## Sprint S2 (1.5h) — Claude Code 适配器 Spike

**目标**: 验证 Claude Code ACP 协议在非 TTY 环境可用性。

### 文件清单

| # | 操作 | 文件 | 说明 |
|:-:|:-----|:-----|:------|
| 1 | **修改** | `backend/app/runtime/code_capable/claude_adapter.py` | 补全 health_check + capability + generate_plan |

### 方法实现

```python
class ClaudeCodeAdapter(CodeCapableAdapter):
    runtime_type = "claude-code"       # 统一连字符命名

    async def health_check(self) -> HealthResult:
        """运行 claude --version"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "claude", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
            version = stdout.decode().strip()
            return HealthResult(online=True, runtime_type="claude-code",
                                version=version, capabilities=["code_generation"])
        except Exception as e:
            return HealthResult(online=False, runtime_type="claude-code",
                                version="unavailable", error=str(e), capabilities=[])

    async def generate_plan(self, problem: str, context: dict) -> PlanResult:
        """运行 claude --acp --stdio 生成计划（如果不可用，记录并返回不可用结果）"""
        try:
            # ACP 模式调用
            ...
        except Exception as e:
            # 记录 experimental_unavailable，不阻塞
            return PlanResult(
                plan_summary="[CLAUDECODE UNAVAILABLE] Claude Code ACP mode is not "
                             "available in this environment. Falling back to Codex.",
                impact_scope="N/A",
                risk_level="low",
                files_expected=[],
                raw_output=f"Claude Code ACP unavailable: {e}",
            )
```

### 降级路径

如果 Claude Code 不可用：

- `health_check()` 返回 `online=False, version="unavailable"`
- `generate_plan()` 返回明确的不可用消息而非报错
- registry 中 `enabled` 保持 `0`，`claude-code` 状态标记为 `experimental_unavailable`
- v0.9.2 整体不阻塞

### 验证

| # | 操作 | 预期 |
|:-:|:-----|:-----|
| 1 | `claude --version` | ✅/❌ 输出版本或 command not found |
| 2 | `claude --acp --stdio` 非交互 | ✅/❌ 记录结果 |
| 3 | health_check 返回 | ONLINE 或 OFFLINE + version string |
| 4 | generate_plan 返回 | 计划文本或不可用消息 |
| 5 | `GET /api/v1/runtimes` 含 claude-code | 状态显示 experimental |

---

## Sprint S3 (1h) — Runtime Endpoint Config

**目标**: 在 seed_runtimes.py 中注册 3 个 disabled 云端 runtime，验证不影响启动。

### 文件清单

| # | 操作 | 文件 | 说明 |
|:-:|:-----|:-----|:------|
| 1 | **修改** | `backend/app/runtime/seed_runtimes.py` | +3 disabled runtime |

### 新增 disabled runtime

```python
{
    "runtime_id": "cloud-openclaw",
    "runtime_type": "openclaw",
    "display_name": "OpenClaw (Cloud)",
    "adapter_module": "app.runtime.adapters.external_http_adapter",
    "endpoint": "https://openclaw.example.com",  # 占位 URL
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
```

### 行为

- disabled runtime 注册到 `runtime_registry` 表，`enabled=0`
- `GET /api/v1/runtimes` 返回全部 runtime，disabled 的标记 `enabled: false`
- disabled runtime 不执行 health_check，不调用 endpoint
- disabled runtime 不出现在 CCR 的 runtime_id 可选项中
- 现有 enabled runtime（hermes-local、openclaw-local、codex）不受影响

### 验证

| # | 操作 | 预期 |
|:-:|:-----|:-----|
| 1 | 重启后端 | 启动正常，无网络连接错误 |
| 2 | `GET /api/v1/runtimes` | 返回 7 个 runtime（4 enabled + 3 disabled） |
| 3 | disabled runtime 的 `enabled` | 均为 `false` |
| 4 | 现有 enabled runtime | hermes/openclaw/codex 健康检查正常 |
| 5 | 后端日志 | 无"连接云端超时"等异常日志 |

---

## Sprint S4 (1h) — CCR runtime_id 参数

**目标**: CCR 创建时支持 `runtime_id` 参数，默认 `codex`，非法/disabled 返回错误。

### 文件清单

| # | 操作 | 文件 | 说明 |
|:-:|:-----|:-----|:------|
| 1 | **修改** | `backend/app/schemas/code_change_request.py` | runtime_id 可选字段 |
| 2 | **修改** | `backend/app/routers/code_change_requests.py` | 创建 + 验证 + 状态机 guard |

### API 变更

**创建 CCR** (`POST /api/v1/code-change-requests`):

```json
{
    "source_type": "execution_request",
    "source_id": "1",
    "execution_request_id": 1,
    "runtime_id": "codex",           // 新增可选，默认 "codex"
    "title": "...",
    "problem_summary": "..."
}
```

**行为**:

| 场景 | 行为 |
|:-----|:-----|
| 不传 `runtime_id` | 默认 `codex` |
| 传 `runtime_id=codex` | ✅ 正常 |
| 传 `runtime_id=claude-code` | ✅ 允许（但 generate_patch/apply 拒绝） |
| 传 `runtime_id=cloud-hermes` | ❌ 422 — `"Runtime 'cloud-hermes' is disabled"` |
| 传 `runtime_id=nonexistent` | ❌ 422 — `"Runtime 'nonexistent' not found"` |
| 传 `runtime_id=claude-code` + `generate-patch` | ❌ 422 — `"Runtime 'claude-code' is experimental and does not support patch generation"` |

**不后退降级**: 上述错误情况不 silent fallback 到 codex，直接返回明确错误。

### 验证

| # | 操作 | 预期 |
|:-:|:-----|:-----|
| 1 | POST CCR 不传 runtime_id | 创建成功，runtime_id=codex |
| 2 | POST CCR 传 runtime_id=codex | 创建成功 |
| 3 | POST CCR 传 runtime_id=claude-code | 创建成功 |
| 4 | POST CCR 传 runtime_id=cloud-hermes | 422 错误 |
| 5 | POST CCR 传 runtime_id=invalid | 422 错误 |
| 6 | claude-code CCR 调用 generate-patch | 422 错误 |
| 7 | claude-code CCR 调用 generate-plan | ✅ 允许（ Spike 路径） |
| 8 | codex CCR 完整链路不变 | plan→patch→checks→apply→rollback 正常 |

---

## 不做检查清单

| 功能 | 确认 | 备注 |
|:-----|:----:|:-----|
| 前端 Runtime 选择 UI | ❌ | API 层即可 |
| Auto 选择 | ❌ | 数据不足 |
| 对比执行 | ❌ | 成本高 + 状态机复杂 |
| 云端 Agent 真实执行 | ❌ | execute() 硬禁用 |
| 阿里/MiniMax 真实对接 | ❌ | 仅 disabled config |
| Agent marketplace | ❌ | 不在路线 |
| 多租户 | ❌ | 不在路线 |
| 自动调度 | ❌ | 不在路线 |

---

## 验收总清单

| # | 验收项 | Sprint | 验证方式 |
|:-:|:-------|:------:|:---------|
| 1 | ExternalHTTPAgentAdapter 模板完成 | S1 | 文件存在 + 方法签名正确 |
| 2 | mock cloud agent health_check + capability 成功 | S1 | mock server → API → 返回 ONLINE |
| 3 | endpoint_url 安全校验：合法/非法 URL | S1 | ValueError 测试 |
| 4 | execute() 硬禁用，不 POST 到远程 | S1 | 始终返回 unsupported |
| 5 | auth token 不进 config（仅环境变量） | S1 | 代码审查 |
| 6 | enabled=false 不触达远程 | S1+S3 | health_check_local() 不发起 HTTP |
| 7 | Claude Code health_check + capability | S2 | 成功或记录 unavailable |
| 8 | Claude Code generate_plan spike | S2 | 成功或记录不可用消息 |
| 9 | cloud-openclaw / cloud-hermes / minimax-agent 注册 | S3 | GET /runtimes 返回 + enabled=false |
| 10 | disabled runtime 不影响启动 | S3 | 重启无异常日志 |
| 11 | CCR API 支持 runtime_id，默认 codex | S4 | 不传 → codex；传 value → 对应 runtime |
| 12 | disabled runtime 返回 422 | S4 | 明确错误，不 fallback |
| 13 | experimental runtime patch/apply 拒绝 | S4 | 422 + 解释 |
| 14 | Codex 主链路不受影响 | S4 | 完整 plan→patch→checks→apply→rollback |
| 15 | 不改前端 UI | 全局 | `git diff --stat frontend/` 无变化 |

---

## Sprint 顺序依赖

```
S1 (2h) ──→ S3 (1h) ──→ S4 (1h)
  │                      ↑
  └──→ S2 (1.5h) ───────┘
```

- S1 和 S2 可并行（互不依赖）
- S3 依赖 S1（ExternalHTTPAgentAdapter 模板）
- S4 依赖 S3（runtime registry 需要含 claude-code）
