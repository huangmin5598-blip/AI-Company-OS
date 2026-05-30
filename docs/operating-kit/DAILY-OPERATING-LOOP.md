---
title: "Daily Operating Loop — AI Company OS 每日运营循环"
domain: operating-kit
---

# Daily Operating Loop — 每日运营循环

> **对应版本**：v0.17  
> **核心文件**：`scripts/run_operating_loop.py`, `backend/app/services/scheduler.py`, `backend/app/services/ceo_brief.py`  
> **前置**：已配置 `backend/config/scheduled_work_orders.yaml`

---

## 1. 流程总览

```
09:00 launchd / manual
    │
    ▼
[1] Load scheduled_work_orders.yaml
    │
    ▼
[2] Check due tasks (cadence: daily/weekly/monthly)
    │
    ▼
[3] Dedup check (same scheduled_id once per day, unless --force)
    │
    ▼
[4] Runtime Health Check (OpenClaw / Codex / Ollama)
    │
    ▼
[5] Budget Guard (check token thresholds)
    │
    ▼
[6] Create Work Order(s) for due tasks
    │
    ▼
[7] Route + Execute (or queue for async)
    │
    ▼
[8] Failure Policy (classify results)
    │
    ▼
[9] Generate CEO Brief (8 sections, Markdown)
    │
    ▼
[10] Register event in Run Ledger + Asset Registry
```

---

## 2. 配置

### 定时任务配置

文件：`backend/config/scheduled_work_orders.yaml`

```yaml
scheduled_work_orders:
  - id: "daily-system-health-brief"
    task_type: "system_health"
    cadence: "daily"
    time: "09:00"
    prompt: "Generate a brief health summary..."
    expected_output: "Markdown health brief"
    skill_id: "system_health"
    approval_required: false
```

### 参数

| 字段 | 类型 | 说明 |
|:-----|:------|:------|
| `id` | string | 唯一标识，用于去重 |
| `task_type` | string | 映射到 Skill Registry 中的 task_type |
| `cadence` | string | daily / weekly / monthly |
| `time` | string | 触发时间（目前仅为文档标记，launchd 控制实际时间） |
| `prompt` | string | 发送给执行器的 prompt |
| `expected_output` | string | 预期产出描述 |
| `skill_id` | string | 对应 skill_registry.yaml 中的 skill |
| `approval_required` | bool | 是否需要 Founder 审批 |

---

## 3. CLI 用法

### 预览模式（不执行任何操作）

```bash
python3 scripts/run_operating_loop.py --dry-run
```

预览输出：显示到期任务、Health Check 结果、预算状态、预计创建的 Work Order，但不执行。生成带 `DRY-RUN` 标记的 CEO Brief。

### 执行模式（执行到期任务）

```bash
python3 scripts/run_operating_loop.py --once
```

### 跳过去重（同一天重复执行）

```bash
python3 scripts/run_operating_loop.py --once --force
```

### 等待异步结果

```bash
python3 scripts/run_operating_loop.py --once --wait-results --timeout 120
```

### 扫描未处理 Work Orders

```bash
python3 scripts/run_operating_loop.py --once --scan-pending
```

---

## 4. CEO Brief 结构

Brief 是一个 8 段式 Markdown 报告，由 `backend/app/services/ceo_brief.py` 自动生成：

| 段落 | 内容来源 |
|:-----|:---------|
| 1. 运行摘要 | 日期、任务数量、运行时长 |
| 2. Runtime Health | Health Check 结果 |
| 3. Work Orders 状态 | 本次创建的 WO 及其状态 |
| 4. 费用汇总 | Token 消耗预估 |
| 5. Budget & Failure Warnings | Budget 超限告警、故障策略执行结果 |
| 6. 重要发现 | 系统自动检测到的异常或趋势 |
| 7. Founder 决策项 | 需要 Founder 确认的事项 |
| 8. 下一步建议 | 系统自动推荐的下一个动作 |

### 存放位置

```
reports/ceo-briefs/
├── INDEX.md                  # 所有 Brief 索引
├── YYYY-MM-DD.md             # 日简报
└── DRY-RUN-YYYY-MM-DD.md    # 预览简报
```

---

## 5. 角色分工

| 角色 | 职责 |
|:-----|:------|
| **Scheduler** | 加载配置、判断到期、去重 |
| **Health Checker** | 检查各运行时是否可用 |
| **Budget Guard** | 检查 Token 消耗是否超限 |
| **CEO Brief Generator** | 收集数据并生成 Markdown 报告 |
| **Run Ledger** | 记录每个步骤的事件 |
| **Founder**（人） | 阅读 Brief → 做决策 |

---

## 6. 当前限制

- 不自动部署到 launchd（需手动配置）
- 仅支持手动 `--once` 和 `--dry-run` 模式
- 不支持多 cadence 在同一运行中交错执行
- 不扫描已存在的 pending Work Orders（除非 `--scan-pending`）
- 定时时间由 `launchd` / `cron` 控制，而非系统内部精确调度
