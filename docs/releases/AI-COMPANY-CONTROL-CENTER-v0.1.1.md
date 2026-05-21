# AI Company Control Center v0.1.1 — Release Notes

> **Release Date**: 2026-05-21
> **Version**: v0.1.1
> **Tags**: [`v0.1.1-p0`](https://github.com/tangbomao/ai-company-os/tree/v0.1.1-p0) → [`v0.1.1`](https://github.com/tangbomao/ai-company-os/tree/v0.1.1)
> **Previous**: v0.1 (只读看板 — Phase 1~7 + Phase 0.4)

---

## 版本目标

v0.1.1 不新增功能，**专攻数据可信化与安全边界加固**。

v0.1 构建了 Control Center 的完整功能骨架（9 张表、27 个 API 端点、9 个前端页面、内嵌 Hermes Chat），但核心数据层存在 **mock 数据与真实数据混合**的问题，且写操作端点缺乏安全边界。

**v0.1.1 的目标：**
- P0 — 数据可信化：mock 隔离、真实数据刷新、API 默认只返回 real
- P1 — 安全边界：写操作三态门禁、Alpha 分层标识、command_logs 记录

---

## 完成内容

### P0：数据可信化（8/8 通过）

| # | 检查项 | 结果 |
|:-:|:-------|:----:|
| 1 | `GET /api/v1/runs` 返回真实数据，不含 mock | ✅ 14 条真实执行记录 |
| 2 | `GET /api/v1/costs` 返回真实成本，不含 mock | ✅ 6 项 Agent 成本 |
| 3 | `GET /api/v1/alerts` 返回真实告警，不含 mock | ✅ 6 条未解决告警 |
| 4 | Agent 三维状态 | ✅ discovery / activity / health 独立判定 |
| 5 | Refresh 不污染 mock | ✅ 先清除旧 real，再同步 |
| 6 | Command 默认 dry-run | ✅ 返回 `status=dry-run` |
| 7 | `ALLOW_ALPHA_WRITE=false` 拒绝 execute | ✅ 返回 403 |
| 8 | command_logs 已记录 | ✅ 4 条记录（dry-run / rejected） |

### P1：前端 + 安全边界

| 模块 | 内容 | 状态 |
|:-----|:-----|:----:|
| Agent 三维状态 3D Badge | 前端 Agent 卡片显示 Registered/Unregistered + Active/Inactive + OK/Warning/Error | ✅ |
| 写端点 Safety Gate | 3 个写端点全部实现 dry-run 默认 + `ALLOW_ALPHA_WRITE` + `X-Confirm` 三态门禁 | ✅ |
| command_logs 全覆盖 | 所有写操作记录到 `command_logs` 表 | ✅ |
| 前端 Alpha 标识 | Command Center 和 Chat Panel 导航栏标注黄色 `Alpha` | ✅ |
| 功能分层 | Stable Core: Dashboard / Agents / Runs / Costs / Alerts | ✅ |
| | Alpha: Command Center / Hermes Chat Panel | ✅ |

---

## 真实数据指标

### 执行记录（14 条）

```
scheduler-2026-04-22  | passed | 2026-04-22
test-run-v1           | passed | 2026-04-18
test-run-legacy       | passed | 2026-04-18
obs-1-deterministic   | passed | 2026-04-18
obs-2-deterministic   | passed | 2026-04-18
obs-3-deterministic   | passed | 2026-04-18
test-memory-writeback | passed | 2026-04-18
test-memory-recall-2  | passed | 2026-04-18
run-1-novel           | passed | 2026-04-18
run-2-novel           | passed | 2026-04-18
run-4-novel           | passed | 2026-04-18
test-flow-001         | passed | 2026-04-17
option-b-test-001     | passed | 2026-04-17
scheduler-2026-05-01  | passed | 2026-04-17
```

**数据来源**: `run-ledger-v1/db/production-flow-ledger.json`
**结果分布**: 14/14 passed（100%）

### 成本数据（6 项 Agent 成本）

| Agent | 调用次数 | 总成本 (USD) | 平均单次成本 |
|:------|:--------:|:------------:|:-----------:|
| story-editor | 6 | $0.00508 | $0.00085 |
| research-agent | 4 | $0.00150 | $0.00038 |
| finance-analyst | 3 | $0.00114 | $0.00038 |
| writer | 2 | $0.00086 | $0.00043 |
| lead-novel | 2 | $0.00082 | $0.00041 |
| review-editor | 2 | $0.00080 | $0.00040 |
| **合计** | **19** | **$0.01020** | — |

**数据来源**: `gateway-lite/cost-view/by-agent.json`

### 告警（6 条未解决）

| 严重级别 | 标题 | 来源 |
|:--------:|:-----|:-----|
| 🔴 error | 外围市场动态-周末 执行失败 | cron（连续 3 次报错） |
| 🟡 warning | 金融摘要-交易日早间 执行失败 | cron |
| 🟡 warning | 亚马逊选品报告-周五 执行失败 | cron（AxiosError 400） |
| 🟡 warning | 亚马逊选品报告-周二 执行失败 | cron（AxiosError 400） |
| 🔴 error | 金融投资摘要 执行失败 | cron（连续 7 次报错） |
| 🟡 warning | 亚马逊选品报告 执行失败 | cron |

**数据来源**: Alert Detector 自动扫描 cron 错误 + 执行失败

### Agent 状态（18 个）

| 状态 | 数量 | 说明 |
|:-----|:----:|:-----|
| `registered / inactive / warning` | 15 | 目录存在 + 已注册 |
| `unregistered / inactive / warning` | 3 | 目录存在但 CLI 未注册 |
| `online` | 15 | 运行时在线 |
| `offline` | 3 | builder-core, demand-miner, creative-lab |

**统计摘要**:
```
Agent 总数:   18
在线 Agent:   15
离线 Agent:    3
忙碌 Agent:    0
业务线:        5（运行中 3, 异常 1）
本月成本:    $0.00
执行总数:    14
失败执行:     0
未解决告警:   6
```

---

## Mock 数据隔离机制

| 措施 | 状态 | 说明 |
|:-----|:----:|:------|
| `data_source` 字段 | ✅ | 5 张表已加字段（execution_records, artifacts, cost_snapshots, alerts, cron_jobs） |
| API 默认过滤 | ✅ | 所有路由器默认 `.filter(data_source != 'mock')` |
| 调试模式 | ✅ | 支持 `?include_mock=true` 查询参数 |
| Refresh 清除策略 | ✅ | 每次 refresh 前清除旧 real 数据，防止混合 |
| Seed 标记 | ✅ | seed.py 中所有数据标记为 `data_source='mock'` |

**典型 Refresh 流程**:
```
POST /api/v1/refresh
  → 清除旧 real 记录
  → 从 OpenClaw 读取真实数据
  → 写入 DB（标记 data_source='real'）
  → 返回同步结果
  → API 默认只返回 data_source != 'mock'
```

---

## Agent 三维状态说明

Control Center 对每个 Agent 维护 **三个独立状态维度**：

```
Agent 状态 = (discovery_status, activity_status, health_status)
```

| 维度 | 状态值 | 判定逻辑 |
|:-----|:-------|:---------|
| **discovery_status** | `registered` | `openclaw agents list` CLI 返回 |
| | `unregistered` | 目录 `~/.openclaw/agents/{name}/` 存在但 CLI 未注册 |
| | `discovered` | 仅目录存在（预留） |
| **activity_status** | `active` | 过去 7 天内有执行记录 |
| | `inactive` | 7 天内无任何运行记录 |
| **health_status** | `ok` | 关联运行正常 |
| | `warning` | 存在但近期无数据 |
| | `error` | 关联 cron job 或 execution 有 failed/error |

**前端 3D Badge 示例**:
```
[registered] [inactive] [warning]  ← main (openclaw, MiniMax-M2.5)
[unregistered] [inactive] [warning] ← builder-core (未注册)
```

---

## Command Center Alpha 安全边界

Command Center（指挥台）是 Phase 5 引入的实验性功能，v0.1.1 之前无写操作保护。

### 三态安全门禁

```
        ┌─ mode=dry-run（默认）
        │    → 返回分析报告
        │    → 不创建任务，不调 Agent
POST    │
/command│
        └─ mode=execute
              ├─ ALLOW_ALPHA_WRITE=false → 403 + command_log(rejected)
              └─ ALLOW_ALPHA_WRITE=true
                     ├─ 缺少 X-Confirm: yes → 400 + command_log(rejected)
                     └─ X-Confirm: yes → 执行 + command_log(executed)
```

### 3 个受保护写端点

| 端点 | 方法 | 安全级别 |
|:-----|:----:|:--------:|
| `/api/v1/agents/{name}` | PATCH | ⚠️ 需全部三态 |
| `/api/v1/tasks/{id}` + `/cancel` + `/retry` | POST/PATCH | ⚠️ 需全部三态 |
| `/api/v1/command` | POST | ⚠️ 需全部三态 |

### 前端 Alpha 标识

- **Command Center 页面**: 导航栏黄色 `Alpha` 标签
- **Hermes Chat Panel**: 侧边栏黄色 `Alpha` 标签
- **Stable Core 页面**（Dashboard / Agents / Runs / Costs / Alerts）: 无标签

---

## 已知限制

| # | 问题 | 影响 | 计划 |
|:-:|:-----|:-----|:-----|
| 1 | **artifact-ledger.json JSON 解析错误** | 5 条 artifact 仍为 mock | 等待源文件修复 |
| 2 | **仅 1 个 Agent (main) 被 CLI 注册** | 17 个其它 Agent 不可通过指挥台调度 | 业务决策 — 是否需全部注册 |
| 3 | **成本数据仅到 2026-03-30** | 每日成本趋势不可用 | P2-lite 修复 |
| 4 | **对话面板无上下文感知** | 每轮对话独立，不能理解当前页面状态 | P2-lite 修复 |
| 5 | **前端 `?include_mock=true` 未实现切换按钮** | 仅后端支持，前端无 UI 切换 | 低优先级 |

---

## 下一步计划

### v0.1.2 / P2-lite（候选）

| 工作项 | 预估 | 优先级 |
|:-------|:----:|:------:|
| 成本数据同步修复（补充近期每日成本） | 0.5 天 | P2 |
| Hermes Chat Panel 上下文感知 | 0.5 天 | P2 |
| artifact-ledger 解析修复 | 0.25 天 | P2 |

### v0.2 路线（待定）

- TASK-POOL + Approval Center（统一任务池 + 审批面板）
- 暂不排期，等待 Founder 决策

---

## 截图归档

| 页面 | 文件 |
|:-----|:-----|
| 🏠 总览 Dashboard | `docs/assets/screenshots/v0.1.1-dashboard.png` |
| 🤖 Agent 列表 | `docs/assets/screenshots/v0.1.1-agents.png` |
| 📋 执行记录 | `docs/assets/screenshots/v0.1.1-runs.png` |
| ⚡ Command Center Alpha | `docs/assets/screenshots/v0.1.1-command-center-alpha.png` |

---

> **AI Company Control Center v0.1.1 — 数据可信、安全可控**  
> 从"看起来有数据"到"数据是真的"。  
> 从"谁都可以写"到"三重门禁保护"。
