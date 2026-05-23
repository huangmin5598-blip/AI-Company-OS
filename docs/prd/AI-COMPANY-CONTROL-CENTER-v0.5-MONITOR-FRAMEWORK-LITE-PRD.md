# AI Company Control Center v0.5 — Monitor Framework Lite PRD

> **状态**: 📋 PRD · 待执行
> **预估工时**: 8-10h（约 2 天冲刺，分 Sprint A + Sprint B）
> **定位**: v0.5 让 AI Company OS 第一次具备"自我观察"能力：系统定期只读扫描任务、成本、执行记录和 Runtime 状态，发现异常后生成 Monitor Finding，并把需要处理的问题送入现有 Company Loop。
>
> **一句话**: v0.5 = Monitor Framework Lite — 让系统开始"主动看见自己"。
>
> **核心子系统**: Monitor Framework（Probes → Analyzers → Findings → Outputs）

---

## 一、产品定位

### 从"记住过去"到"观察现在"

| 版本 | 核心能力 | 系统状态 |
|:-----|:---------|:---------|
| v0.2 | Company Loop MVP | 系统能**执行**任务闭环 |
| v0.3 | CEO Agent Lite | 系统能**理解** Founder 意图 |
| v0.4 | Company Memory MVP | 系统能**记住**过去的经验 |
| **v0.5** | **Monitor Framework Lite** | 系统能**观察**自己的运行状态 |

### 主链路

```
Monitor Scan (manual trigger)
  ↓
Probes:
  task_probe → 读取 task_pool
  cost_probe → 读取 cost_snapshots
  execution_probe → 读取 execution_records
  runtime_probe → 通过 RuntimeAdapter Protocol 做 health_check
  ↓
Analyzers:
  stuck_task_analyzer → 发现长时间未推进的任务
  cost_spike_analyzer → 发现成本异常上升
  error_rate_analyzer → 发现最近执行失败率异常
  ↓
Findings:
  monitor_finding 写入 → severity (info / warning / critical)
  ↓
Outputs:
  info → 只写 finding
  warning → finding + alert (source=monitor)
  critical → finding + alert + task draft (status=approval_required)
```

### 回答的问题

> **系统能自己发现需要 Founder 关注的问题吗？**

v0.2-v0.4 让系统能**执行、决策、记忆**。
v0.5 回答：**"系统能不能主动看见自己哪里不对劲，并告诉 Founder？"**

---

## 二、范围

### 必做

| 模块 | 说明 | 工时 |
|:-----|:------|:----:|
| Config | `config/monitor-rules.example.yaml` | 0.5h |
| Models | `monitor_runs` + `monitor_findings` 表 | 1h |
| Probes | task_probe + cost_probe + execution_probe + runtime_probe | 2.5h |
| Analyzers | stuck_task + cost_spike + error_rate | 2h |
| Outputs | finding 写入 + alert 创建 + 可选 task draft | 2h |
| APIs | POST run / GET runs / GET findings / dismiss / create-task | 1.5h |
| 验收 | 3 条验收标准 | 0.5h |

### 不做

- ❌ 自动修复
- ❌ 自动执行
- ❌ 自动审批
- ❌ 多 Runtime 完整接入
- ❌ 复杂 UI Dashboard
- ❌ 通知渠道集成
- ❌ Agent Meeting
- ❌ Paperclip 集成
- ❌ 定时调度（v0.5 仅手动触发）

---

## 三、Probes 设计

### task_probe

读取 `task_pool` 表，查找：
- `status = 'in_progress'` 且 `updated_at` 超过阈值（默认 2h）
- `status = 'pending_approval'` 且 `updated_at` 超过阈值（默认 4h）
- `status = 'in_review'` 且 `updated_at` 超过阈值（默认 4h）

输出: `list[TaskStuckData]` — 每个 stuck task 的 id, status, title, hours_since_update

### cost_probe

读取 `cost_snapshots` 表，按时间窗口聚合：
- 最近 24h 平均每小时代价
- 之前 24h 平均每小时代价
- 计算变化比率

输出: `CostSpikeData` — 当前成本、历史成本、变化倍率

### execution_probe

读取 `execution_records` 表：
- 最近 N 条记录（默认 20）
- 统计成功/失败/超时比例
- 收集失败原因文本

输出: `ErrorRateData` — 总执行数、失败数、失败率、最近失败记录

### runtime_probe

通过 `RuntimeAdapter Protocol` 的 `health_check()` 方法：
- 调用每个已注册 Runtime 的健康检查
- 收集状态（online/offline/degraded）

输出: `list[RuntimeHealthData]` — 每个 runtime 的名称、类型、状态

---

## 四、Analyzers 设计

### stuck_task_analyzer

**输入**: task_probe 输出
**逻辑**: 对每个 stuck task，按超过阈值时间分 severity
**严重度**:

| 超过阈值 | Severity |
|:---------|:---------|
| < 2x 阈值 | info |
| 2x-4x 阈值 | warning |
| > 4x 阈值 | critical |

**输出**: `list[MonitorFinding]`

### cost_spike_analyzer

**输入**: cost_probe 输出
**逻辑**: 如果当前成本 > 历史平均 × threshold_multiplier（默认 2.0）
**严重度**:

| 变化倍率 | Severity |
|:---------|:---------|
| 1.5x - 2.0x | info |
| 2.0x - 3.0x | warning |
| > 3.0x | critical |

**输出**: `MonitorFinding | None`

### error_rate_analyzer

**输入**: execution_probe 输出
**逻辑**: 如果失败率 > error_threshold（默认 30%）
**严重度**:

| 失败率 | Severity |
|:-------|:---------|
| 10% - 30% | info |
| 30% - 50% | warning |
| > 50% | critical |

**输出**: `MonitorFinding | None`

---

## 五、Outputs 设计

### Severity → Action 映射

| Severity | Actions |
|:---------|:--------|
| `info` | 只写 `monitor_finding` |
| `warning` | 写 `monitor_finding` + 创建 `alert` (source=monitor) |
| `critical` | 写 `monitor_finding` + 创建 `alert` + 创建 `task draft` (approval_required) |

### Alert 规范

创建的 alert:
```json
{
  "severity": "warning",
  "title": "Stuck task: Market Research Project",
  "description": "Task #42 has been 'in_progress' for 3.5 hours (threshold: 2h).",
  "source": "monitor",
  "source_id": "monitor_finding:{finding_id}"
}
```

### Task Draft 规范

critical 级别可选的 task draft 写在 `task_pool`:
```json
{
  "title": "Investigate: Stuck task - Market Research Project",
  "description": "Monitor detected task #42 stuck for 4+ hours. Review and decide action.",
  "status": "approval_required",
  "source": "monitor",
  "source_id": "monitor_finding:{finding_id}"
}
```

---

## 六、数据模型

### monitor_runs

```sql
CREATE TABLE monitor_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL DEFAULT 'running',
    -- success / failed / partial
    summary TEXT,
    findings_count INTEGER DEFAULT 0,
    alerts_created INTEGER DEFAULT 0,
    tasks_created INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);
```

### monitor_findings

```sql
CREATE TABLE monitor_findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    monitor_run_id INTEGER NOT NULL,
    finding_type TEXT NOT NULL,
    -- stuck_task / cost_spike / error_rate / runtime_health
    severity TEXT NOT NULL DEFAULT 'info',
    title TEXT NOT NULL,
    summary TEXT,
    evidence_json TEXT,
    -- structured evidence data
    status TEXT NOT NULL DEFAULT 'open',
    -- open / acknowledged / dismissed / converted
    source_id TEXT,
    -- e.g. "task:42", "cost:snapshot:5"
    alert_id INTEGER,
    task_id INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (monitor_run_id) REFERENCES monitor_runs(id)
);
```

---

## 七、API 端点

| Method | Path | Description |
|:-------|:-----|:------------|
| POST | `/api/v1/monitor/run` | 手动触发一次 monitor scan |
| GET | `/api/v1/monitor/runs` | 查看历史 monitor runs |
| GET | `/api/v1/monitor/runs/{id}` | 查看单次 run 详情（含 findings）|
| GET | `/api/v1/monitor/findings` | 查看 findings（可过滤 status/severity/type）|
| GET | `/api/v1/monitor/findings/{id}` | 查看单个 finding 及 evidence |
| PATCH | `/api/v1/monitor/findings/{id}/dismiss` | Founder 关闭某个 finding |
| POST | `/api/v1/monitor/findings/{id}/create-task` | 将 finding 转成 task draft |

---

## 八、验收标准

### 验收 1: Stuck Task

**输入**: 构造一个 `status='in_progress'` 且超过 2h 未更新的 task

**结果**:
- ✅ `monitor_run` 新增，status=success
- ✅ `monitor_finding` 新增，finding_type=stuck_task, severity=critical
- ✅ `alert` 新增，source=monitor
- ✅ 可选 task draft 进入 task_pool，status=approval_required

### 验收 2: Cost Spike

**输入**: 构造最近成本明显高于历史平均

**结果**:
- ✅ `monitor_finding` 新增，finding_type=cost_spike
- ✅ severity = warning 或 critical（按倍率）
- ✅ `alert` 新增

### 验收 3: Error Rate

**输入**: 构造最近 execution_records 中失败率超过 30%

**结果**:
- ✅ `monitor_finding` 新增，finding_type=error_rate
- ✅ 关联 evidence_json 包含失败记录样本
- ✅ `alert` 新增

### 通用验收

- ✅ 所有 finding 都有关联的 `evidence_json`
- ✅ 不触发任何 execute（只读扫描）
- ✅ API 端点全部可访问并返回预期结果

---

## 九、执行计划

```
Sprint A (~5h)
├── Config: monitor-rules.example.yaml
├── Models: monitor_runs + monitor_findings
├── Probes: task_probe + cost_probe
├── Analyzers: stuck_task + cost_spike
├── Outputs: findings + alerts
└── 验收：Stuck Task + Cost Spike

Sprint B (~4h)
├── Probes: execution_probe + runtime_probe
├── Analyzers: error_rate
├── Outputs: task draft (approval_required)
├── APIs: 5 endpoints
├── Config: 依赖 RuntimeAdapter 的示例配置
└── 验收：Error Rate + 全链路
```

---

> **本文档是 v0.5 Monitor Framework Lite 的产品需求文档。**
> 每个模块交付前，需 Founder 确认范围、排期、验收标准。
> v0.5 不做自动修复、自动执行、自动审批。
