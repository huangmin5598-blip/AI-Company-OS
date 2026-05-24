# v0.6 Runtime Layer MVP — 执行计划

> **基于 PRD**: `AI-COMPANY-CONTROL-CENTER-v0.6-RUNTIME-LAYER-MVP-PRD.md`
> **预估工时**: 8-10h（Sprint A ~4h + Sprint B ~2.5h + Sprint C ~2h）
> **前置条件**: v0.5 Monitor Framework 已上线；OpenClaw Gateway 运行在 localhost:18789；Hermes CLI 已安装

---

## 执行概览

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
├── Step 8: Heartbeat 记录集成到 runner
├── Step 9: 验证 runtime_health finding 生成
└── Step 10: config 示例更新

Sprint C (~2h) — Frontend
├── Step 11: Agents 页面按 Runtime 分组
└── Step 12: 全链路验收
```

---

## Sprint A: Core Runtime Layer

### Step 1: Models

**新文件**: `backend/app/models/runtime_registry.py`
**新文件**: `backend/app/models/runtime_heartbeat.py`
**修改**: `backend/app/models/__init__.py`

#### runtime_registry.py

```python
# @PRODUCT Model — OS Core
from sqlalchemy import Column, String, Integer, Text, DateTime, func
from app.models.base import Base


class RuntimeRegistry(Base):
    """Registered runtime instances."""

    __tablename__ = "runtime_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    runtime_id = Column(String, nullable=False, unique=True, index=True)
    runtime_type = Column(String, nullable=False)
    # hermes / openclaw / codex / claude_code / cloud
    display_name = Column(String, nullable=False)
    adapter_module = Column(String, nullable=False)
    # Python module path: "app.runtime.adapters.hermes_adapter"
    endpoint = Column(String)
    # CLI path or HTTP URL
    config_json = Column(Text)
    # Optional adapter-specific config
    enabled = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

#### runtime_heartbeat.py

```python
# @PRODUCT Model — OS Core
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, func
from app.models.base import Base


class RuntimeHeartbeat(Base):
    """Health check record for a runtime."""

    __tablename__ = "runtime_heartbeats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    runtime_id = Column(String, ForeignKey("runtime_registry.runtime_id"), nullable=False)
    status = Column(String, nullable=False)
    # online / degraded / offline / unknown
    message = Column(Text)
    latency_ms = Column(Integer)
    capabilities_count = Column(Integer, default=0)
    checked_at = Column(DateTime, nullable=False, default=func.now())
```

### Step 2: registry.py 升级

**修改**: `backend/app/runtime/registry.py`

从内存列表升级为 DB 读写：

```python
# @PRODUCT Runtime registry — OS Core
"""Runtime registry — reads registered runtimes from DB."""

from app.database import get_sync_session
from app.models.runtime_registry import RuntimeRegistry


def get_all_runtime_adapters() -> list[dict]:
    """Return all enabled runtime registrations from DB."""
    session = get_sync_session()
    try:
        rows = session.query(RuntimeRegistry).filter_by(enabled=1).all()
        return [
            {
                "runtime_id": r.runtime_id,
                "runtime_type": r.runtime_type,
                "display_name": r.display_name,
                "adapter_module": r.adapter_module,
                "endpoint": r.endpoint,
            }
            for r in rows
        ]
    finally:
        session.close()


def instantiate_adapter(reg: dict):
    """Dynamically import and instantiate an adapter from its module path."""
    import importlib
    mod_path = reg["adapter_module"]
    mod = importlib.import_module(mod_path)
    return mod.create_adapter(reg)


def get_instantiated_adapters() -> list:
    """Return instantiated adapter objects for all enabled runtimes."""
    registrations = get_all_runtime_adapters()
    return [instantiate_adapter(r) for r in registrations]
```

### Step 3: BaseRuntimeAdapter 基类

**新文件**: `backend/app/runtime/base_adapter.py`

```python
# @PRODUCT Base RuntimeAdapter — OS Core
from typing import Any, Optional
from app.runtime.protocol import RuntimeAdapter, RuntimeStatus


class BaseRuntimeAdapter:
    """Base class for runtime adapters. Subclasses override glue methods."""

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
```

### Step 4: Adapter 实现

**新目录**: `backend/app/runtime/adapters/`
**新文件**: `__init__.py`, `hermes_adapter.py`, `openclaw_adapter.py`

#### hermes_adapter.py

```python
# @PRODUCT Adapter — OS Core
import subprocess
import json
import time
from typing import Optional
from app.runtime.base_adapter import BaseRuntimeAdapter
from app.runtime.protocol import RuntimeStatus, RuntimeCapability


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
                    import re
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
```

#### openclaw_adapter.py — 优先使用 openclaw CLI，目录扫描做 fallback

```python
# @PRODUCT Adapter — OS Core
import json
import time
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
        import subprocess, os, glob

        agent_names = []

        # Primary: openclaw status CLI
        try:
            result = subprocess.run(
                ["openclaw", "status"],
                capture_output=True, text=True, timeout=10,
            )
            for line in result.stdout.split("\n"):
                if "Agents" in line:
                    import re
                    match = re.search(r"Agents\s+[│|]\s+(\d+)", line)
                    if match:
                        agent_count = int(match.group(1))
                        # Try to get names from directory as CLI doesn't list them by name
                        break
        except Exception:
            pass

        # Fallback: scan agents directory
        if not agent_names:
            agents_dir = os.path.expanduser("~/.openclaw/agents")
            if os.path.isdir(agents_dir):
                agent_names = sorted(os.listdir(agents_dir))

        return [
            {"name": "agent_hosting", "type": "multi_agent",
             "description": f"多 Agent 运行 ({len(agent_names)} agents)", "enabled": True,
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
```

#### claude_code_stub.py

```python
# @PRODUCT Adapter — OS Core (placeholder)
from app.runtime.base_adapter import BaseRuntimeAdapter
from app.runtime.protocol import RuntimeStatus


class ClaudeCodeAdapterStub(BaseRuntimeAdapter):
    """Placeholder for future Claude Code integration."""

    @property
    def runtime_type(self) -> str:
        return "claude_code"

    async def health_check(self) -> RuntimeStatus:
        return RuntimeStatus.OFFLINE

    async def get_capabilities(self) -> list[dict]:
        return [
            {"name": "code_generation", "type": "code",
             "description": "代码生成（未接入）", "enabled": False},
            {"name": "code_review", "type": "quality",
             "description": "代码审查（未接入）", "enabled": False},
        ]


def create_adapter(reg: dict):
    return ClaudeCodeAdapterStub(reg["runtime_id"], reg["display_name"])
```

```python
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
        ]


def create_adapter(reg: dict):
    return CodexAdapterStub(reg["runtime_id"], reg["display_name"])
```

### Step 5: Runtime Router

**新文件**: `backend/app/routers/runtime_registry.py`
**修改**: `backend/app/routers/__init__.py`

```python
# @PRODUCT Router — OS Core
import json
from fastapi import APIRouter, HTTPException
from app.database import get_sync_session
from app.models.runtime_registry import RuntimeRegistry
from app.models.runtime_heartbeat import RuntimeHeartbeat
from app.runtime.registry import get_instantiated_adapters, get_all_runtime_adapters

router = APIRouter(prefix="/api/v1/runtimes", tags=["runtimes"])


def _serialize_reg(r):
    return {
        "runtime_id": r.runtime_id,
        "runtime_type": r.runtime_type,
        "display_name": r.display_name,
        "adapter_module": r.adapter_module,
        "endpoint": r.endpoint,
        "enabled": bool(r.enabled),
        "created_at": str(r.created_at),
        "updated_at": str(r.updated_at),
    }


@router.get("")
async def list_runtimes():
    """List all registered runtimes with latest heartbeat."""
    session = get_sync_session()
    try:
        runtimes = session.query(RuntimeRegistry).all()
        result = []
        for r in runtimes:
            reg = _serialize_reg(r)
            # Attach latest heartbeat
            hb = session.query(RuntimeHeartbeat).filter_by(
                runtime_id=r.runtime_id
            ).order_by(RuntimeHeartbeat.checked_at.desc()).first()
            if hb:
                reg["latest_heartbeat"] = {
                    "status": hb.status,
                    "checked_at": str(hb.checked_at),
                    "latency_ms": hb.latency_ms,
                }
            else:
                reg["latest_heartbeat"] = None
            result.append(reg)
        return {"runtimes": result}
    finally:
        session.close()


@router.get("/{runtime_id}")
async def get_runtime(runtime_id: str):
    session = get_sync_session()
    try:
        r = session.query(RuntimeRegistry).filter_by(runtime_id=runtime_id).first()
        if not r:
            raise HTTPException(status_code=404)
        return _serialize_reg(r)
    finally:
        session.close()


@router.get("/{runtime_id}/heartbeats")
async def get_heartbeats(runtime_id: str, limit: int = 20):
    session = get_sync_session()
    try:
        hbs = session.query(RuntimeHeartbeat).filter_by(
            runtime_id=runtime_id
        ).order_by(RuntimeHeartbeat.checked_at.desc()).limit(limit).all()
        return {"heartbeats": [
            {"status": h.status, "message": h.message,
             "latency_ms": h.latency_ms, "checked_at": str(h.checked_at)}
            for h in hbs
        ]}
    finally:
        session.close()


@router.get("/{runtime_id}/capabilities")
async def get_capabilities(runtime_id: str):
    adapters = get_instantiated_adapters()
    for a in adapters:
        if a.runtime_id == runtime_id:
            caps = await a.get_capabilities()
            return {"runtime_id": runtime_id, "capabilities": caps}
    raise HTTPException(status_code=404)


@router.post("/refresh")
async def refresh_all():
    """Force health check on all registered runtimes. Simple: calls runtime_probe.collect directly."""
    from app.monitor.probes.runtime_probe import collect
    results = await collect({})
    return {"runtimes": results}
```

### Step 6: 种子数据

### Step 6: 种子数据（幂等插入）

```sql
-- Codex/Claude Code placeholder 默认 enabled=0，不产生 Monitor 噪音
INSERT OR IGNORE INTO runtime_registry (runtime_id, runtime_type, display_name, adapter_module, endpoint, enabled)
VALUES
  ('hermes-local', 'hermes', 'Hermes Agent', 'app.runtime.adapters.hermes_adapter', NULL, 1),
  ('openclaw-local', 'openclaw', 'OpenClaw Gateway', 'app.runtime.adapters.openclaw_adapter', 'http://localhost:18789', 1),
  ('codex-stub', 'codex', 'Codex', 'app.runtime.adapters.codex_stub', NULL, 0),
  ('claude-code-stub', 'claude_code', 'Claude Code', 'app.runtime.adapters.claude_code_stub', NULL, 0);
```

---

## Sprint B: Monitor Integration

### Step 7: runtime_probe 升级

**修改**: `backend/app/monitor/probes/runtime_probe.py`

```python
# @PRODUCT Probe — OS Core
from app.runtime.registry import get_instantiated_adapters
from app.database import get_sync_session
from app.models.runtime_heartbeat import RuntimeHeartbeat
from datetime import datetime


async def collect(config: dict) -> list[dict]:
    """Check all registered runtimes via their adapters. Records heartbeats."""
    adapters = get_instantiated_adapters()
    results = []
    session = get_sync_session()
    try:
        for adapter in adapters:
            try:
                status = await adapter.health_check()
                caps = await adapter.get_capabilities()
                latency = getattr(adapter, "latency_ms", 0)

                # Record heartbeat
                hb = RuntimeHeartbeat(
                    runtime_id=adapter.runtime_id,
                    status=status.value,
                    latency_ms=latency,
                    capabilities_count=len(caps),
                    checked_at=datetime.utcnow(),
                )
                session.add(hb)
                session.commit()

                results.append({
                    "runtime_id": adapter.runtime_id,
                    "name": adapter.name,
                    "type": adapter.runtime_type,
                    "status": status.value,
                    "latency_ms": latency,
                    "capabilities": caps,
                })
            except Exception as e:
                hb = RuntimeHeartbeat(
                    runtime_id=adapter.runtime_id,
                    status="unknown",
                    message=str(e),
                    checked_at=datetime.utcnow(),
                )
                session.add(hb)
                session.commit()
                results.append({
                    "runtime_id": adapter.runtime_id,
                    "name": getattr(adapter, 'name', 'unknown'),
                    "type": getattr(adapter, 'runtime_type', 'unknown'),
                    "status": "error",
                    "error": str(e),
                })
        return results
    finally:
        session.close()
```

### Step 8: runner 加入 runtime 检查

**修改**: `backend/app/monitor/runner.py`

确保 `run_monitor_scan` 把 runtime_probe 放在靠前的位置，并且使用配置控制启用/禁用：

```python
if config.get("probes", {}).get("runtime_probe", {}).get("enabled", True):
    try:
        from app.monitor.probes.runtime_probe import collect as collect_runtime
        rt_data = await collect_runtime(config)
        for r in rt_data:
            if r["status"] in ("offline", "unknown"):
                all_findings.append({
                    "finding_type": "runtime_health",
                    "severity": "critical" if r["status"] == "offline" else "warning",
                    "title": f"Runtime {r['name']} is {r['status']}",
                    "summary": f"Runtime '{r['name']}' ({r.get('type', '?')}) "
                               f"reported status: {r['status']}.",
                    "evidence_json": r,
                    "source_id": f"runtime:{r['runtime_id']}",
                })
            elif r["status"] == "degraded":
                all_findings.append({
                    "finding_type": "runtime_health",
                    "severity": "warning",
                    "title": f"Runtime {r['name']} is degraded",
                    "summary": f"Runtime '{r['name']}' reported degraded status.",
                    "evidence_json": r,
                    "source_id": f"runtime:{r['runtime_id']}",
                })
    except Exception as e:
        errors.append(f"runtime_probe: {e}")
```

---

## Sprint C: Frontend

### Step 11: Agents 页面按 Runtime 分组

**修改**: `frontend/src/app/agents/page.tsx`

修改点：
1. 页面加载时调用 `GET /api/v1/runtimes` 获取 runtime 列表
2. 对每个 runtime，调 `GET /api/v1/runtimes/{id}/capabilities` 获取能力
3. 按 runtime 分组渲染卡片式布局
4. 每个卡片显示：runtime 名称、当前状态（online/degraded/offline）、能力列表、心跳时间
5. OpenClaw runtime 展开显示 agent 列表（来自 capabilities.agents）

数据结构：

```typescript
interface RuntimeInfo {
  runtime_id: string;
  runtime_type: string;
  display_name: string;
  enabled: boolean;
  latest_heartbeat?: {
    status: string;  // online / degraded / offline
    checked_at: string;
    latency_ms: number;
  };
}

interface RuntimeCapability {
  name: string;
  type: string;
  description: string;
  enabled: boolean;
  agents?: string[];  // For OpenClaw
}
```

---

## 验收流程

### 产品验收

1. **Runtime Registry**: `GET /api/v1/runtimes` 返回 4 个 runtime（Hermes/OpenClaw online，Codex/Claude Code offline）
2. **runtime_probe**: monitor scan 后 runtime_probe 返回真实数据，非空列表
3. **runtime_health finding**: Codex/Claude Code 因 enabled=0 不产生噪音；若某个 real runtime offline，生成 runtime_health finding
4. **Agents 页面**: 按 Runtime 分组展示，保留现有 Agent 卡片内容

### 工程验收

5. **幂等 seed**: 重复执行 seed 不会报错，不会重复创建 runtime
6. **适配器隔离**: Hermes/OpenClaw 任一 adapter 失败，不影响其他 adapter
7. **噪音控制**: Codex/Claude Code placeholder（enabled=0）不产生 runtime_health alert
8. **UI 降级**: Agents 页面仍能看到旧 agent 状态信息，不被 Runtime 分组改丢

```bash
# 1. 创建表
python -c "from app.database import init_db; init_db()"

# 2. 插入种子数据
python -c "
from app.database import get_sync_session
from app.models.runtime_registry import RuntimeRegistry
s = get_sync_session()
runtimes = [
  RuntimeRegistry(runtime_id='hermes-local', runtime_type='hermes',
    display_name='Hermes Agent', adapter_module='app.runtime.adapters.hermes_adapter'),
  RuntimeRegistry(runtime_id='openclaw-local', runtime_type='openclaw',
    display_name='OpenClaw Gateway', adapter_module='app.runtime.adapters.openclaw_adapter',
    endpoint='http://localhost:18789'),
  RuntimeRegistry(runtime_id='codex-stub', runtime_type='codex',
    display_name='Codex', adapter_module='app.runtime.adapters.codex_stub'),
  RuntimeRegistry(runtime_id='claude-code-stub', runtime_type='claude_code',
    display_name='Claude Code', adapter_module='app.runtime.adapters.claude_code_stub'),
]
for r in runtimes: s.add(r)
s.commit()
print('Seeded 4 runtimes')
"

# 3. 运行 monitor scan
curl -X POST http://localhost:8001/api/v1/monitor/run

# 4. 验证 runtime 列表
curl http://localhost:8001/api/v1/runtimes | python3 -m json.tool

# 5. 验证 runtime_health finding
curl http://localhost:8001/api/v1/monitor/findings?finding_type=runtime_health
```

---

## 执行清单

### Sprint A

- [ ] Step 1: 创建 `runtime_registry.py` + `runtime_heartbeat.py` 模型
- [ ] Step 1: 更新 `models/__init__.py`
- [ ] Step 2: 升级 `runtime/registry.py` 为 DB 读写
- [ ] Step 3: 创建 `runtime/base_adapter.py`
- [ ] Step 4: 创建 `runtime/adapters/` 包 + hermes_adapter.py
- [ ] Step 4: 创建 `runtime/adapters/openclaw_adapter.py`
- [ ] Step 5: 创建 `runtime/adapters/codex_stub.py` + `claude_code_stub.py`
- [ ] Step 6: 创建 `routers/runtime_registry.py` + 注册
- [ ] Step 6: 种子数据插入

### Sprint B

- [ ] Step 7: 升级 `monitor/probes/runtime_probe.py`
- [ ] Step 8: 确保 runner 包含 runtime_probe
- [ ] Step 9: 验证 runtime_health finding 生成
- [ ] Step 10: 更新 `config/company-instance.example.yaml`

### Sprint C

- [ ] Step 11: 前端 Agents 页面按 Runtime 分组
- [ ] Step 12: 全链路验收

---

## 风险与回滚

| 风险 | 缓解 |
|:-----|:------|
| `hermes status` 超时 | timeout=15s，捕获 TimeoutExpired → offline |
| OpenClaw 端口变更 | endpoint 在 DB 中可配置，不硬编码 |
| httpx 依赖未安装 | FastAPI 项目已有 httpx（ASGI 依赖） |
| subprocess 调用阻塞 | 每个 adapter 独立执行，不影响其他 probe |
| frontend 改坏 | 备份当前 agents/page.tsx 后再修改 |
