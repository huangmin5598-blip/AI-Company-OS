# Build Log: AI Company Control Center v0.1.1

> **日期**: 2026-05-21  
> **作者**: AI Company OS Team  
> **版本**: v0.1.1 (稳定化)  
> **阅读对象**: 对外公开 — GitHub / 技术社区 / 关注 AI 创业工具栈的开发者

---

## 为什么做 Control Center

2026 年春天，我们面临一个非常"现实"的问题。

我们的 AI Agent 团队已经运行了一段时间——OpenClaw 上有 18 个 Agent，每天执行 Cron 任务，处理小说编辑、金融分析、亚马逊选品、内容管理等业务线。它们是我们的"员工"，但：

- **看不见**——不知道哪些 Agent 在跑、哪些出错了
- **管不住**——没有控制面板，出了问题只能翻日志
- **算不清**——每个月 LLM 花了多少钱？没有统计

这就是 **AI Company Control Center** 的起点。

不是做一个"AI 平台"（市场上已经够多了），而是做一个**一人公司的作战指挥室**——把分散在 CLI、JSON 文件、Cron 配置里的 Agent 状态，汇聚成一个可视化面板。

v0.1 搭建了骨架：9 张表、27 个 API 端点、9 个前端页面。但问题是——**数据是假的**。

---

## v0.1 → v0.1.1：从"看起来有数据"到"数据是真的"

v0.1 的验收报告给我敲了警钟。逐项对账后发现：

| 数据类型 | v0.1 状态 | 真实数据占比 |
|:---------|:---------:|:-----------:|
| Execution Records | ❌ 全是 Mock | **0%** |
| Costs | ⚠️ 混合 | **19%** |
| Alerts | ⚠️ 混合 | **13%** |
| Cron Jobs | ✅ 真实 | **100%** |
| Agents | ⚠️ 口径混淆 | — |

典型场景：用户打开 Dashboard，看到"今日成本 $1.25"，然后发现**这个数字是假数据生成的**。控制面板提供虚假的操作依据，比没有面板更危险。

于是我们砍掉了所有新功能的计划，把 v0.1.1 的 scope 收窄为 **"不说假话"**。

---

## 为什么 mock 数据污染是关键问题

"先跑起来，数据后面再补"——这是很多 MVP 的习惯做法。但在 AI Company OS 里，这个做法有根本性风险：

1. **成本误导** — mock 成本数据可能比真实成本高 10 倍，用户据此做预算决策会出错
2. **告警失聪** — 13 条 mock alert 和 2 条真实 alert 混在一起，用户无法区分哪些需要处理
3. **Agent 数量幻觉** — "管理 18 个 Agent" 听起来很多，实际只有 1 个被 CLI 注册

我们的解决方案不复杂，但很彻底：

- **全局 `data_source` 字段** — 每张表记录每行数据是 `real` 还是 `mock`
- **API 默认过滤** — 所有端点默认 `WHERE data_source != 'mock'`
- **Refresh 先清后写** — 每次同步前清除旧 real 数据，不混合
- **调试模式** — `?include_mock=true` 保留给开发和测试

结果是：**用户看到的所有数字都是真的**。假的不是不存在，而是被明确标记、默认隐藏。

---

## 为什么保留 Command Center Alpha

v0.1 的验收报告还发现了一个边界问题：Phase 5~7 引入了**写操作端点**（指挥台、任务 CRUD、Agent PATCH），超出了 v0.1 "只读"的原始范围。

我们的处理方式：

- ✅ **不删除已有功能** — 用户已经用上了指挥台，回退是破坏性变更
- ✅ **不假装这是 Stable** — 前端明确标注黄色 `Alpha` 标签
- ✅ **三重安全门禁** — dry-run 默认 + `ALLOW_ALPHA_WRITE` 总开关 + `X-Confirm` 确认头
- ✅ **完整审计日志** — 所有写操作（成功/拒绝/模拟）均写入 `command_logs`

**理念**：Alpha 功能可以存在，但用户必须清楚地知道它在哪个风险等级下运行。

---

## 现在系统能证明什么

### 1. Agent 运行是真实的

14 条执行记录全部来自生产 ledger，时间跨度 2026-04-17 至 2026-04-22，100% passed。说明 **OpenClaw 作为 runtime 是稳定的**。

### 2. 成本数据是可控的

6 个 Agent 的 19 次调用，累计成本 **$0.0102**。最贵的 Agent 是 story-editor（$0.00508 / 6 次调用），单次成本约 $0.00085。**一人公司的 AI 运营成本是可以做到很低的**。

### 3. 监控是自动的

6 条未解决告警全部由 Alert Detector 自动生成，覆盖了 cron 执行失败（Amazon 选品报告 400 错误、金融摘要 Message failed、外围市场动态连续失败）。**不需要人工巡检**。

### 4. 安全边界是可配置的

三重门禁机制让写操作在"不信任模式"下默认拒绝。`ALLOW_ALPHA_WRITE=false` 时，任何 execute 操作返回 403。**数据安全不是靠自觉，是靠代码强制**。

---

## 架构截图

```
Frontend (Next.js 14 + Tailwind)     Backend (FastAPI + SQLAlchemy 2.0)
         │                                      │
         │ http://localhost:3001                 │ http://127.0.0.1:8001
         ▼                                      ▼
  ┌───────────────┐                    ┌───────────────────┐
  │  Dashboard     │                    │  REST API (27 端) │
  │  Agents        │◄────── REST ──────►│  Refresh Engine   │
  │  Runs          │                    │  Alert Detector   │
  │  Costs         │                    │  Command Gate     │
  │  Alerts        │                    │  Chat Proxy       │
  │  Command (α)   │                    └────────┬──────────┘
  │  Chat (α)      │                             │
  └───────────────┘                              ▼
                                          ┌──────────────┐
                                          │   SQLite DB  │ ← 11 张表
                                          │   (real+mock)│
                                          └──────┬───────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │  OpenClaw    │ ← CLI + JSON 文件
                                          │  Runtime     │
                                          └──────────────┘
```

### 数据流

```
OpenClaw Cron Jobs  →  jobs.json        →  CRON_JOBS (100% real)
OpenClaw Executions →  flow-ledger.json →  EXECUTION_RECORDS (14 real)
OpenClaw Agents     →  agents list CLI  →  AGENTS (1 registered + 17 discovered)
Gateway Lite Costs  →  cost-view/*.json →  COSTS (6 agents, 19 calls)
Cron Error Scanner  →  alert_detector   →  ALERTS (6 unresolved)
```

---

## 关键数字

| 指标 | 数值 |
|:-----|:----:|
| Agents 总数 | 18 |
| 真实执行记录 | 14 |
| 真实成本条目 | 19 |
| 未解决告警 | 6 |
| Cron Jobs | 21 |
| API 端点 | 27 |
| 前端页面 | 9 |
| 数据库表 | 11 |
| Git Commits | 18 |
| 总代码量 | ~8,000 行 |

---

## 下一步准备做什么

### 短期：v0.1.2 / P2-lite（可选优化）

- **成本数据修复** — 补充近期每日成本，不再只显示 2026-03-30 的旧数据
- **对话面板上下文感知** — Hermes Chat Panel 自动注入当前看板状态，不用用户手动描述
- **Artifact 修复** — 修复 artifact-ledger.json 解析

### 中期：v0.2 — TASK-POOL + Approval Center

- 统一任务池：所有任务显式注册，状态可追踪
- 审批面板：Monitor 建议 / 跨线变更 / 新 Agent 上线
- 执行模式：standard / lite / resume / blocked / skipped

### 远期：v0.3-v0.6

- CEO Agent 上线 → Memory 4 层 → Agent 会议 → 多 Runtime 接入

详见 [`docs/AI-COMPANY-OS-ROADMAP.md`](../AI-COMPANY-OS-ROADMAP.md)

---

## 致谢

这个版本没有引入任何新功能，但它比 v0.1 更重要。

> 数据不真实的面板，是谎言。  
> 数据真实的面板，是证据。  
> **v0.1.1 让这个系统从"产品演示"变成了"运营工具"。**

---

*AI Company Control Center v0.1.1 — 数据可信、安全可控。*  
*2026-05-21 · 上海*
