# AI Company Control Center v0.9.2 — External Runtime Connector MVP PRD

> **状态**: 📋 PRD · 待执行
> **预估工时**: 4-6h
> **定位**: v0.9.2 让 AI Company OS 可以用统一 RuntimeAdapter 模型接入**本地 Agent、云端 Agent、代码 Agent 和第三方 Agent Runtime**，建立统一接入边界。
>
> **一句话**: v0.9.2 不是让所有 Agent 干活，而是证明"同一套 RuntimeAdapter 模型能接任何 Agent"。

---

## 一、产品定位

### 从"只接本地 Codex"到"统一接任何 Runtime"

| 版本 | 核心能力 | Agent 来源 |
|:-----|:---------|:-----------|
| v0.6 | Runtime Layer MVP | 注册 + 健康检查 + 发现 | 本地 Hermes / OpenClaw |
| v0.9 | Code-Capable Runtime Bridge | 安全代码修改流水线 | 本地 Codex（+ Claude Code 骨架） |
| **v0.9.1** | Code Bridge 产品化 | --output-schema + git apply --check | Codex |
| **v0.9.2** | **External Runtime Connector MVP** | **统一接入模板 + Claude Code Spike + Config 扩展** | **本地 + 云端 + 代码 Runtime** |

### 为什么要现在做

当前 AI Company OS 能管理 4 个 Runtime（Hermes、OpenClaw、Codex、Claude Code），但：

1. **Claude Code 还是骨架** — `enabled=0`，没有真实调用能力
2. **没有云端 Agent 接入模板** — 云端 Hermes、云端 OpenClaw、阿里、MiniMax 要接入得各写一套
3. **CCR 硬编码 Codex** — Founder 没有选择 Runtime 的能力

v0.9.2 不做"所有 Agent 都能干活"，而是建立**统一接入边界**：注册 → 健康检查 → 能力发现 → 成本读取。

### 版本命名变化

> v0.9.2 原名 **External Intelligence Agent MVP**，GPT 分析后纠正为 **External Runtime Connector MVP**。
> "外部情报/研究 Agent"（GitHub / arXiv / Web 情报）另开 v0.9.3，不混入本版本。

---

## 二、范围

### 必做

| # | 模块 | 说明 | 工时 |
|:-:|:-----|:------|:----:|
| 1 | **ExternalHTTPAgentAdapter 模板** | 通用 HTTP Adapter 基类，6 个标准方法，mock cloud agent 验证 | 2h |
| 2 | **Claude Code 适配器 Spike** | health_check + capability discovery + generate_plan 验证 | 1.5h |
| 3 | **Runtime Endpoint Config** | cloud-openclaw / cloud-hermes / minimax-agent disabled 注册 | 1h |
| 4 | **CCR runtime_id 参数** | 创建时可选 runtime_id，默认 codex，disabled/不存在报错 | 1h |

### 必做详情

#### 1. ExternalHTTPAgentAdapter 模板

**文件**: `backend/app/runtime/adapters/external_http_adapter.py`

实现 `RuntimeAdapter` 协议的标准 HTTP 模板：

```python
class ExternalHTTPAgentAdapter:
    """通用外部 HTTP Agent 适配器模板。

    支持通过 endpoint_url + auth_type 连接任何外部 Agent Runtime。
    用于：云端 OpenClaw、云端 Hermes、阿里云端 Agent、MiniMax 云端 Agent、自建 Agent。
    """

    def __init__(self, runtime_id, runtime_type, display_name, endpoint_url,
                 auth_type="none", health_path="/health", capabilities_path="/capabilities",
                 execute_path="/execute", cost_path="/cost", enabled=False,
                 risk_level="medium", timeout_seconds=300):
```

**标准字段**:

| 字段 | 类型 | 必填 | 说明 |
|:-----|:-----|:----:|:-----|
| `runtime_id` | string | ✅ | 唯一标识 |
| `runtime_type` | string | ✅ | Agent 类型 |
| `display_name` | string | ✅ | 显示名称 |
| `endpoint_url` | string | ✅ | Agent API 基地址 |
| `auth_type` | string | ✅ | `none` / `bearer_token` / `api_key` / `custom` |
| `health_path` | string | ❌ | 默认 `/health` |
| `capabilities_path` | string | ❌ | 默认 `/capabilities` |
| `execute_path` | string | ❌ | 默认 `/execute` |
| `cost_path` | string | ❌ | 默认 `/cost` |
| `enabled` | bool | ❌ | 默认 `False` |
| `risk_level` | string | ❌ | `low` / `medium` / `high` |
| `timeout_seconds` | int | ❌ | 默认 `300` |

**标准方法**:

| 方法 | 实现 |
|:-----|:-----|
| `health_check()` | GET `{endpoint_url}{health_path}` → 200 → ONLINE |
| `get_capabilities()` | GET `{endpoint_url}{capabilities_path}` → 能力列表 |
| `get_cost()` | GET `{endpoint_url}{cost_path}` → tokens / cost |
| `create_session()` | 返回 stub session（云端执行未做时） |
| `execute()` | **硬禁用远程执行** — 始终返回 `unsupported`，不 POST 到远程 `/execute` |
| `cancel_session()` | 返回 stub |

**安全边界**:

① **execute() 硬禁用远程执行** — 即使配置了 `execute_path`，`execute()` 也只返回 `{"status": "unsupported", "detail": "Remote execution is disabled in v0.9.2"}`。不 POST 请求到远程 `/execute` 端点。

② **auth token 不进配置** — config 只保存 `auth_type` 和 `auth_env`（环境变量名，如 `CLOUD_HERMES_TOKEN`）。真实 token 仅来自环境变量，不写入 config.yaml / git 跟踪的文件。

③ **endpoint_url 安全校验** — 只允许：
   - `http://localhost:*`
   - `http://127.0.0.1:*`
   - `https://*`
   
   禁止：`file://`、`ftp://`、`http://[metadata-ip]`（如 169.254.169.254）、`ws://`、`wss://` 等非标准协议。

④ **enabled=false 的 runtime 不触达远程** — 不执行 health_check，不调用 endpoint。registry 中只标记 `registered` / `disabled`，不产生网络请求。

**Mock Cloud Agent 验证**: 启动一个简单的 mock HTTP server 跑通一次 health_check + capability discovery。

#### 2. Claude Code 适配器 Spike

**文件**: `backend/app/runtime/code_capable/claude_adapter.py`

| 方法 | 目标 |
|:-----|:-----|
| `health_check()` | 运行 `claude --version` → 成功 → ONLINE |
| `get_capabilities()` | 返回 `[CODE_GENERATION, TOOL_USE]` |
| `generate_plan(problem, context)` | 运行 `claude --acp --stdio` 生成 plan_summary |
| `generate_patch()` | ❌ 不做（保留 enabled=0） |

**Spike 边界**:
- 如果本机没有 `claude` CLI 或 ACP 在非 TTY 环境不可用，记录为 `experimental_unavailable`，**不阻塞 v0.9.2**
- 能跑通则记录为 `experimental_available`
- enabled 保持 `0`，不在 CCR 中开放 patch/apply
- runtime_id **全 PRD / API / error message 统一使用 `claude-code`**（连字符），不混用 `claude_code` 或 `claudeCode`

#### 3. Runtime Endpoint Config

**文件**: `backend/app/runtime/seed_runtimes.py` 扩展

新增 disabled runtime 注册（不启动，但 registry 可见）：

```python
{
    "runtime_id": "cloud-openclaw",
    "runtime_type": "openclaw",
    "display_name": "OpenClaw (Cloud)",
    "adapter_module": "app.runtime.adapters.external_http_adapter",
    "endpoint": "https://xxx.example.com",
    "enabled": 0,  # disabled — just registered
},
{
    "runtime_id": "cloud-hermes",
    "runtime_type": "hermes",
    "display_name": "Hermes (Cloud)",
    "adapter_module": "app.runtime.adapters.external_http_adapter",
    "endpoint": "https://xxx.example.com",
    "enabled": 0,
},
{
    "runtime_id": "minimax-agent",
    "runtime_type": "cloud_agent",
    "display_name": "MiniMax Agent",
    "adapter_module": "app.runtime.adapters.external_http_adapter",
    "endpoint": "https://api.example.com/agent",
    "enabled": 0,
},
```

**行为**:
- disabled runtime 注册后，`GET /api/v1/runtimes` 返回但标记 `enabled: false`
- disabled runtime 不影响系统启动
- disabled runtime 不在 CCR 可选项中出现
- 不影响现有稳定链路（Hermes、OpenClaw、Codex 的 enabled 不变）

#### 4. CCR runtime_id 参数

**文件**: `backend/app/routers/code_change_requests.py`

- 创建 CCR 时接受可选 `runtime_id` 字段
- 默认 `codex`（保持不变）
- `runtime_id` 不存在或 `enabled=0` → 返回 `422` 明确错误
- `runtime_id = claude_code` → 只允许 `generate_plan`，`generate_patch`/`apply` 返回错误：
  ```json
  {"detail": "Runtime 'claude_code' is experimental and does not support patch generation"}
  ```
- 不 silent fallback 到 codex

**不做**:
- 前端 Runtime 选择器（后置）
- Auto 选择（后置）

### 不做

| 功能 | 原因 |
|:-----|:-----|
| 前端 Runtime 选择 UI | API 层证明可用性即可，UI 后置 |
| Runtime 自动选择 | 数据不足，后置 v0.9.3+ |
| Codex / Claude 对比执行 | 成本翻倍 + 状态机复杂化，后置 v1.1+ |
| 云端 Agent 真实执行 | 模板 + mock 验证即可，真实执行后置 |
| Agent marketplace | 不在当前路线 |
| 多租户 | 不在当前路线 |
| 自动调度 | 不在当前路线 |
| Agent Meeting | v1.0 规划 |
| 阿里 / MiniMax 真实对接 | 需逐家确认 API 文档，后置 |

---

## 三、当前 Runtime 底座

现有已注册 Runtime（不重写，只扩展）：

| Runtime ID | 类型 | 状态 | 连接 |
|:-----------|:-----|:----:|:-----|
| `hermes-local` | Hermes | ✅ enabled | 本地 CLI |
| `openclaw-local` | OpenClaw | ✅ enabled | `localhost:18789` |
| `codex` | Codex | ✅ enabled | 本地 CLI |
| `claude-code` | Claude Code | ⏸️ experimental | enabled=0 → spike 验证 |
| `cloud-openclaw` | OpenClaw | 🔲 disabled | 新增，config only |
| `cloud-hermes` | Hermes | 🔲 disabled | 新增，config only |
| `minimax-agent` | MiniMax | 🔲 disabled | 新增，config only |

---

## 四、架构变化

```
v0.9.2 新增/修改：
───────────────────────────────────────────────────────
backend/app/runtime/
├── adapters/
│   └── external_http_adapter.py    [新增] 通用 HTTP Agent 模板
├── code_capable/
│   └── claude_adapter.py           [修改] health + capability + plan spike
└── seed_runtimes.py                [修改] +3 disabled runtime

backend/app/routers/
└── code_change_requests.py         [修改] runtime_id 参数

backend/app/schemas/
└── code_change_request.py          [修改] runtime_id 可选字段
```

**不改**:
- `protocol.py` — RuntimeAdapter 协议不变
- `base_adapter.py` — 不变
- `factory.py` — 不变（code_capable factory 不涉 external HTTP）
- `patch_generator.py` — 不变
- `codex_adapter.py` — 不变
- `mock_adapter.py` — 不变
- 所有前端文件 — 不变

---

## 五、验收标准

| # | 验收项 | 验证方式 |
|:-:|:-------|:---------|
| 1 | ExternalHTTPAgentAdapter 模板完成 | 文件存在 + 方法签名正确 |
| 2 | mock cloud agent health_check + capability discovery 成功 | 启动 mock server → API 调用 → 返回 ONLINE + 能力列表 |
| 3 | cloud-openclaw / cloud-hermes / minimax-agent disabled config 可注册 | `GET /api/v1/runtimes` 返回以上 3 个且 `enabled: false` |
| 4 | Claude Code health_check + capability discovery 成功 | `GET /api/v1/runtimes` 返回 claude-code 状态 |
| 5 | Claude Code generate_plan 验证 | 调用一次，记录结果（可用/不可用） |
| 6 | CCR API 支持 runtime_id，默认 codex | 不传 runtime_id → codex；传有效值 → 对应 runtime |
| 7 | disabled runtime 返回明确错误 | `runtime_id=cloud-hermes` → 422 + 错误信息 |
| 8 | experimental runtime patch/apply 被拒绝 | `runtime_id=claude-code` generate_patch → 422 + 解释 |
| 9 | 不改前端 UI | `git diff --stat frontend/` 无变化 |
| 10 | 不改现有稳定 Code Bridge 主链路 | Codex 的 plan→patch→checks→apply→rollback 不变 |

---

## 六、路线衔接

| 版本 | 核心 | 关系 |
|:-----|:-----|:-----|
| v0.9 | Code-Capable Runtime Bridge | 本版本的底座 — Codex 链路 + Claude Code 骨架 |
| v0.9.1 | Schema Patch Integration | Code Bridge 产品化，已交付 |
| **v0.9.2** | **External Runtime Connector MVP** | **统一接入模板 + Claude Code Spike + Config 扩展** |
| v0.9.3 | External Intelligence Agent MVP | 外部情报输入（GitHub/arXiv/RSS/X/Web） |
| v1.0 | Agent Meeting Session | 多 Agent 结构化协作 |

---

> **相关文档**
> - Roadmap: `docs/AI-COMPANY-OS-ROADMAP.md`
> - v0.9 PRD: `docs/prd/AI-COMPANY-CONTROL-CENTER-v0.9-CODE-CAPABLE-RUNTIME-BRIDGE-MVP-PRD.md`
> - v0.6 Runtime Layer MVP PRD: `docs/prd/AI-COMPANY-CONTROL-CENTER-v0.6-RUNTIME-LAYER-MVP-PRD.md`
