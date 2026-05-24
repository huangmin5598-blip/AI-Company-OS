# AI Company Control Center v0.6 — Runtime Layer MVP PRD

> **状态**: 📋 PRD · 待执行
> **预估工时**: 8-10h（约 2 天冲刺，分 Sprint A + Sprint B + Sprint C）
> **定位**: v0.6 将 RuntimeAdapter Protocol 从架构文档落地为真实运行时注册与只读状态层，让 AI Company OS 能统一识别、检查和展示本地 Hermes、本地 OpenClaw 以及未来 Runtime 的运行状态。
>
> **一句话**: v0.6 = Runtime Layer MVP — 让系统知道"我有哪些身体器官"。
>
> **核心子系统**: Runtime Adapter Protocol（Registry → Adapter → Heartbeat → Capabilities → Monitor → UI）

---

## 一、产品定位

### 从"观察自己"到"知道自己有什么"

| 版本 | 核心能力 | 系统状态 |
|:-----|:---------|:---------|
| v0.4.1 | 定义了 RuntimeAdapter Protocol | 协议存在，无实现 |
| v0.5 | Monitor Framework 需要 runtime_probe | runtime_probe 返回空列表 |
| **v0.6** | **Runtime Layer MVP** | **runtime_probe 有真实数据可查** |
| v0.7 | Controlled Self-Improvement | 基于运行时状态做受控改进 |

### 为什么要现在做

v0.5 的 runtime_probe 现在返回空列表。

这意味着：
- Monitor Framework 有 4 个 probe，其中 runtime 那个是 dummy
- 系统不知道当前有哪些 Runtime 在运行
- Agents 页面不知道 agent 属于哪个 Runtime
- CEO Agent 做决策时没有运行时上下文

**v0.6 把 v0.4.1 的协议和 v0.5 的监控桥接在一起。**

---

## 二、范围

### 必做

| 模块 | 说明 | 工时 |
|:-----|:------|:----:|
| Runtime Registry | `runtime_registry` 表，注册所有已知 Runtime | 1h |
| `runtime/registry.py` 升级 | 从空列表改为读写 DB | 0.5h |
| LocalHermesAdapter | `hermes status` CLI → health + capabilities | 1.5h |
| LocalOpenClawAdapter | `GET /health` HTTP → health + capabilities | 1.5h |
| Codex/Claude Code placeholder | 占位 adapter，返回 OFFLINE | 0.5h |
| Runtime Heartbeat | 定期记录 health check 结果 | 1h |
| Capability Discovery | 每个 adapter 返回可用能力列表 | 1h |
| runtime_probe 接入 | 升级 v0.5 probe 使用真实 adapter | 0.5h |
| Agents 页面按 Runtime 分组 | 前端升级，按 runtime 分组展示 | 2h |

### 不做

- ❌ 多 Runtime 自动调度
- ❌ 自动执行
- ❌ 自动修复
- ❌ 自动 kill / restart
- ❌ Codex / Claude Code 真实接入（仅 placeholder）
- ❌ cloud deployment
- ❌ runtime marketplace
- ❌ 跨 Runtime 自动路由
- ❌ 绕过 Command Center / Approval Center

---

## 三、系统设计

### 3.1 主线链路

```
系统启动 / 定时
  ↓
Runtime Registry 读取已注册的 Runtime 列表
  ↓
每个 Runtime → Adapter.health_check() → 写 heartbeat 记录
  ↓
每个 Runtime → Adapter.get_capabilities() → 缓存
  ↓
Monitor runtime_probe 读取 heartbeat 最新记录
  ↓
runtime_health finding（如有 offline/degraded）
  ↓
Agents 页面按 runtime 分组展示
```

### 3.2 Runtime Registry 表

```sql
CREATE TABLE runtime_registry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    runtime_id TEXT NOT NULL UNIQUE,
    runtime_type TEXT NOT NULL,
    -- hermes / openclaw / codex / claude_code / cloud
    display_name TEXT NOT NULL,
    adapter_module TEXT NOT NULL,
    -- Python module path: "app.runtime.adapters.hermes_adapter"
    endpoint TEXT,
    -- CLI path or HTTP URL
    config_json TEXT,
    -- Optional adapter-specific config
    enabled INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### 3.3 Runtime Heartbeat 表

```sql
CREATE TABLE runtime_heartbeats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    runtime_id TEXT NOT NULL,
    status TEXT NOT NULL,
    -- online / degraded / offline / unknown
    message TEXT,
    latency_ms INTEGER,
    capabilities_count INTEGER DEFAULT 0,
    checked_at TEXT NOT NULL,
    FOREIGN KEY (runtime_id) REFERENCES runtime_registry(runtime_id)
);
```

### 3.4 Capability 结构

每个 adapter 返回的 capabilities 结构：

```json
{
  "runtime_id": "hermes-local",
  "capabilities": [
    {
      "name": "chat",
      "type": "conversation",
      "description": "对话交互与任务执行",
      "enabled": true
    },
    {
      "name": "tools",
      "type": "tool_execution",
      "description": "30+ Hermes 工具调用",
      "enabled": true
    },
    {
      "name": "skills",
      "type": "skill_loading",
      "description": "80+ Skills 加载",
      "enabled": true
    }
  ]
}
```

---

## 四、Adapter 实现设计

### 4.1 BaseAdapter 升级

从 `RuntimeAdapter` 协议（v0.4.1）升级为可实例化的基类：

```python
class BaseRuntimeAdapter:
    """Base class for runtime adapters. Implements RuntimeAdapter protocol."""

    @property
    def name(self) -> str: ...

    @property
    def runtime_type(self) -> str: ...

    async def health_check(self) -> RuntimeStatus: ...

    async def get_capabilities(self) -> list[RuntimeCapability]: ...

    async def create_session(self, goal, context) -> RuntimeSession: ...

    async def execute(self, session, command, timeout) -> dict: ...

    async def cancel_session(self, session_id) -> bool: ...

    async def get_cost(self, session_id) -> dict: ...
```

### 4.2 LocalHermesAdapter

```
Source:    hermes status CLI (subprocess)
Health:    解析 CLI 输出 → 判断上线/离线
Capabilities: 扫描 skills/ 目录 + config.yaml
Cost:     暂不支持（返回空）
Session:  暂不支持执行（v0.6 只做只读）
```

**健康检查判别**：

| CLI 输出特征 | Status |
|:------------|:-------|
| 进程运行 + status 返回正常 | online |
| 进程运行但 status 有错误 | degraded |
| 进程未运行 / status 超时 | offline |

### 4.3 LocalOpenClawAdapter

```
Source:    GET http://localhost:18789/health (HTTP)
Health:    {"ok":true,"status":"live"} → online
Capabilities: openclaw status + agents/ 目录 → agent 列表
Cost:     openclaw.json 中的 model cost 配置
Session:  暂不支持执行（v0.6 只做只读）
```

**健康检查判别**：

| HTTP 响应 | Status |
|:----------|:-------|
| 200 + `"ok":true,"status":"live"` | online |
| 200 + 其他状态 | degraded |
| 连接失败 / 超时 | offline |

### 4.4 CodexAdapterStub / ClaudeCodeAdapterStub

```python
class CodexAdapterStub(BaseRuntimeAdapter):
    async def health_check(self):
        return RuntimeStatus.OFFLINE  # Not connected yet

    async def get_capabilities(self):
        return [{"name": "code_generation", "type": "code", ...}]
```

---

## 五、升级后的 runtime_probe

v0.5 的 `runtime_probe` 现在改为从 `Runtime Registry` 读取真实 adapter：

```python
async def collect(config: dict) -> list[dict]:
    adapters = get_all_runtime_adapters()  # Now reads from DB
    results = []
    for adapter in adapters:
        if not adapter.enabled:
            continue
        try:
            status = await adapter.health_check()
            capabilities = await adapter.get_capabilities()
            results.append({
                "runtime_id": adapter.runtime_id,
                "name": adapter.name,
                "type": adapter.runtime_type,
                "status": status.value,
                "capabilities": capabilities,
            })
        except Exception as e:
            ...
    return results
```

---

## 六、前端设计：Agents 页面的 Runtime 分组

### 当前状态

Agents 页面展示扁平列表：Agent Name / Type / Status。

### v0.6 升级后

```
┌─ Runtime: Hermes Agent ───────────────────────────┐
│  CEO Agent         │ chat, tools, skills │ online │
│  ───────────────────────────────────────────────── │
│  Skills available: 80+                             │
│  Last heartbeat: 2m ago                            │
└────────────────────────────────────────────────────┘

┌─ Runtime: OpenClaw Gateway ───────────────────────┐
│  amazon-seller     │ research, analysis  │ online │
│  content-manager   │ content, editorial  │ online │
│  finance-analyst   │ analysis, reporting │ online │
│  writer            │ creative, writing   │ online │
│  +11 more agents   │                     │        │
│  ───────────────────────────────────────────────── │
│  Agents: 15 · Sessions: 176 · Last heartbeat: 30s │
└────────────────────────────────────────────────────┘

┌─ Runtime: Codex (stub) ───────────────────────────┐
│  Not connected      │ code, review, PRs  │ offline│
└────────────────────────────────────────────────────┘

┌─ Runtime: Claude Code (stub) ─────────────────────┐
│  Not connected      │ code, review, PRs  │ offline│
└────────────────────────────────────────────────────┘
```

---

## 七、新增/修改文件

| 文件 | 操作 | 说明 |
|:-----|:-----|:------|
| `backend/app/models/runtime_registry.py` | **New** | Runtime Registry 模型 |
| `backend/app/models/runtime_heartbeat.py` | **New** | Runtime Heartbeat 模型 |
| `backend/app/runtime/registry.py` | **Modify** | 升级为 DB 读写 |
| `backend/app/runtime/base_adapter.py` | **New** | BaseRuntimeAdapter 基类 |
| `backend/app/runtime/adapters/__init__.py` | **New** | Adapter 包 |
| `backend/app/runtime/adapters/hermes_adapter.py` | **New** | LocalHermesAdapter |
| `backend/app/runtime/adapters/openclaw_adapter.py` | **New** | LocalOpenClawAdapter |
| `backend/app/runtime/adapters/codex_stub.py` | **New** | CodexAdapterStub |
| `backend/app/runtime/adapters/claude_code_stub.py` | **New** | ClaudeCodeAdapterStub |
| `backend/app/monitor/probes/runtime_probe.py` | **Modify** | 使用真实 adapter |
| `backend/app/routers/runtime_registry.py` | **New** | Registry 管理 API |
| `backend/app/routers/runtime_heartbeat.py` | **New** | Heartbeat 查询 API |
| `frontend/src/app/agents/page.tsx` | **Modify** | Runtime 分组展示 |
| `config/company-instance.example.yaml` | **Modify** | 注册 runtime 示例 |

---

## 八、API 端点

| Method | Path | Description |
|:-------|:-----|:------------|
| GET | `/api/v1/runtimes` | 列出所有已注册 Runtime |
| GET | `/api/v1/runtimes/{id}` | 查看单个 Runtime 详情 |
| GET | `/api/v1/runtimes/{id}/heartbeats` | 查看 Runtime 心跳历史 |
| GET | `/api/v1/runtimes/{id}/capabilities` | 查看 Runtime 能力列表 |
| POST | `/api/v1/runtimes/refresh` | 强制刷新所有 Runtime 状态 |

---

## 九、验收标准

### 验收 1: Runtime Registry

**输入**: 系统启动后，registry 中有 Hermes + OpenClaw + 2 个 stub

**结果**:
- ✅ `GET /api/v1/runtimes` 返回 4 个 runtime
- ✅ 每个 runtime 有正确的 runtime_id / type / display_name

### 验收 2: runtime_probe 返回真实数据

**输入**: 触发 POST /api/v1/monitor/run

**结果**:
- ✅ runtime_probe 结果不为空
- ✅ Hermes status = online（或 degraded）
- ✅ OpenClaw status = online
- ✅ Codex/Claude Code stub status = offline

### 验收 3: Monitor Framework 生成 runtime_health finding

**输入**: Codex stub 被标记为 offline

**结果**:
- ✅ monitor_finding 存在 finding_type=runtime_health
- ✅ severity = warning 或 critical
- ✅ evidence_json 包含 runtime_id 和状态详情

### 验收 4: Agents 页面按 Runtime 分组

**输入**: 访问 `/agents` 页面

**结果**:
- ✅ Agent 按 Runtime 分组展示
- ✅ 每个分组显示 runtime 名称和心跳状态
- ✅ Stub runtime 显示 "Not connected"

---

## 十、执行计划

```
Sprint A (~4h) — Core Runtime Layer
├── Step 1: Models — runtime_registry + runtime_heartbeat
├── Step 2: registry.py 升级为 DB 读写
├── Step 3: BaseRuntimeAdapter 基类
├── Step 4: LocalHermesAdapter + LocalOpenClawAdapter
├── Step 5: CodexStub + ClaudeCodeStub
└── Step 6: Runtime Router (list / detail / heartbeats / capabilities / refresh)

Sprint B (~2.5h) — Monitor Integration
├── Step 7: runtime_probe 升级
├── Step 8: Runtime Heartbeat 定时记录
├── Step 9: 验证 runtime_health finding 生成
└── Step 10: config/company-instance.example.yaml 示例更新

Sprint C (~2h) — Frontend
├── Step 11: Agents 页面按 Runtime 分组
└── Step 12: 全链路验收
```

---

> **本文档是 v0.6 Runtime Layer MVP 的产品需求文档。**
> v0.6 不做多 Runtime 自动调度、自动执行、自动修复。
> Codex / Claude Code 仅做 placeholder，不做真实接入。
