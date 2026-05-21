# AI Company Control Center v0.1 — 验收报告

> **报告日期**: 2026-05-21
> **报告人**: Hermes Agent
> **状态**: 🔴 **待修复问题后方可通过**

---

## 1. 当前运行状态

| 项目 | 值 |
|:-----|:----|
| 后端 API | `http://127.0.0.1:8001` (FastAPI) |
| 前端 Dashboard | `http://localhost:3001` (Next.js) |
| API 文档 | `http://127.0.0.1:8001/docs` (Swagger) |
| SQLite 数据库 | `~/Documents/Codex/ai-company-os/backend/data/ai_company_os.db` (128KB) |
| Git 分支 | `main` |
| 最新 commit | `db9791e` — docs: AI Company OS 品牌统一 + 宪法 + 路线图 |
| 总 commit 数 | **15** |

### 15 个 commit 摘要（按时间正序）

| # | Hash | 内容 |
|:-:|:-----|:-----|
| 1 | `8aedb66` | initial: project scaffold |
| 2 | `b61e3ac` | phase0-1: data scan report + full backend (models/seed/routers/API) |
| 3 | `31c92b6` | phase2: frontend dashboard (3 pages, dark theme, API client) |
| 4 | `03fc2d4` | phase3: openclaw adapters (agents/cron/ledger/cost/alert) + real data sync |
| 5 | `37eb3c7` | phase4: verification + error handling + README |
| 6 | `4087cee` | v0.1: 外网访问改造 - Serveo tunnel + 前端代理 rewrite |
| 7 | `00422f9` | docs: 更新 PRD + 任务卡 (v0.2 含技能地图 Phase 6.5) |
| 8 | `8278cac` | phase5: 指挥台系统 — 任务CRUD + Command API + 前端页面 |
| 9 | `c504b4c` | phase6: 任务看板 — Kanban 视图 + 任务详情页 + 筛选器 |
| 10 | `186cbe9` | phase6.5: 技能地图 + 成本趋势图 |
| 11 | `756adda` | phase7: 闭环反馈系统 — 失败重试 + 分析仪表板 + 缺口提醒 |
| 12 | `09f1e14` | phase0.4: 对话面板 — Control Center 内嵌 Hermes Chat |
| 13 | `db9791e` | docs: AI Company OS 品牌统一 + 宪法 + 路线图 |

> 注：commit 5 (`37eb3c7`) 后新增了 Phase 5~7，这些扩展了 v0.1 原定范围（新增了指挥台/看板/分析等写操作功能）。本报告按当前实际代码状态验收，并在第 5 节中评估边界合规性。

---

## 2. 已完成模块清单

### 2.1 数据源扫描

| 数据源 | 路径 | 状态 |
|:-------|:-----|:----:|
| Agent 列表 | `openclaw agents list` CLI | ✅ 可调用，已实现 |
| Cron Jobs | `~/.openclaw/cron/jobs.json` | ✅ 直接读取 |
| 生产链记录 | `run-ledger-v1/db/production-flow-ledger.json` | ✅ 已实现，但 schema 不匹配 |
| Artifact 记录 | `run-ledger-v1/db/artifact-ledger.json` | ✅ 已实现，但文件有 JSON 解析错误 |
| 成本按 Model | `cost-view/by-model.json` | ✅ 已实现 |
| 成本按 Agent | `cost-view/by-agent.json` | ✅ 已实现 |
| 成本按 Project | `cost-view/by-project.json` | ✅ 已实现 |
| 每日成本 | `daily/*.json` | ✅ 已实现 |
| 业务线注册 | `BUSINESS-LINE-REGISTRY.md` | ✅ 已实现 |

### 2.2 数据库（9 张 SQLite 表）

| 表 | 行数 | 说明 |
|:---|:----:|:-----|
| `agents` | 15 | Agent 信息 |
| `cron_jobs` | 21 | Cron Job 配置 |
| `business_lines` | 5 | 业务线定义 |
| `execution_records` | 30 | 执行记录 |
| `artifacts` | 5 | 产物记录 |
| `cost_snapshots` | 99 | 成本快照 |
| `alerts` | 15 | CEO 提醒 |
| `refresh_log` | 4 | 刷新日志 |
| `session_events` | 0 | 预留事件表 |
| `tasks` | 10 | 任务（含对话面板会话） |
| `task_messages` | 11 | 任务消息 |

### 2.3 REST API

| 端点 | 方法 | 状态 |
|:-----|:----:|:----:|
| `/api/v1/health` | GET | ✅ |
| `/api/v1/stats` | GET | ✅ |
| `/api/v1/agents` | GET | ✅ |
| `/api/v1/agents/{name}` | GET | ✅ |
| `/api/v1/agents/{name}` | PATCH | ⚠️ 写操作 (Phase 7) |
| `/api/v1/business-lines` | GET | ✅ |
| `/api/v1/business-lines/{id}/runs` | GET | ✅ |
| `/api/v1/runs` | GET | ✅ |
| `/api/v1/runs/{run_id}` | GET | ✅ |
| `/api/v1/artifacts` | GET | ✅ |
| `/api/v1/costs` | GET | ✅ |
| `/api/v1/costs/trend` | GET | ✅ |
| `/api/v1/costs/daily` | GET | ✅ |
| `/api/v1/cron-jobs` | GET | ✅ |
| `/api/v1/alerts` | GET | ✅ |
| `/api/v1/refresh` | POST | ✅ |
| `/api/v1/refresh/status` | GET | ✅ |
| `/api/v1/tasks` | GET/POST | ⚠️ 含写操作 (Phase 5) |
| `/api/v1/tasks/{id}` | GET/PATCH | ⚠️ 含写操作 (Phase 5) |
| `/api/v1/tasks/{id}/cancel` | POST | ⚠️ 写操作 (Phase 5) |
| `/api/v1/tasks/{id}/retry` | POST | ⚠️ 写操作 (Phase 7) |
| `/api/v1/command` | POST | ⚠️ 指挥台写操作 (Phase 5) |
| `/api/v1/chat` | POST | ✅ 对话面板 |
| `/api/v1/chat/sessions` | GET | ✅ |
| `/api/v1/chat/sessions/{id}` | GET/DELETE | ✅ |
| `/api/v1/skills` | GET | ✅ |
| `/api/v1/analysis/failures` | GET | ✅ |
| `/api/v1/analysis/gaps` | GET | ✅ |
| `/api/v1/monitor/insights` | GET | ✅ (骨架) |

> ⚠️ **边界问题**: Phase 5/6/7 引入了写操作端点（PATCH agents、POST/PATCH tasks、POST command、POST retry），超出了 v0.1 "只读" 的原始范围。详见第 5 节。

### 2.4 前端页面

| 页面 | 路由 | 状态 |
|:-----|:-----|:----:|
| 总览 Dashboard | `/` | ✅ |
| Agent 列表 | `/agents` | ✅ |
| 执行记录 | `/runs` | ✅ |
| 指挥台 | `/command` | ⚠️ Phase 5 扩展 |
| 任务看板 | `/tasks` | ⚠️ Phase 6 扩展 |
| 任务详情 | `/tasks/[id]` | ⚠️ Phase 6 扩展 |
| 技能地图 | `/skills` | ⚠️ Phase 6.5 扩展 |
| 分析 | `/analysis` | ⚠️ Phase 7 扩展 |
| 对话 | `/chat` | ✅ Phase 0.4 |

### 2.5 Hermes 内嵌对话面板

| 功能 | 状态 |
|:-----|:----:|
| POST /api/v1/chat | ✅ 调 Hermes CLI 实时回复 |
| 会话列表 GET /api/v1/chat/sessions | ✅ |
| 会话详情 GET /api/v1/chat/sessions/{id} | ✅ |
| 会话删除 DELETE /api/v1/chat/sessions/{id} | ✅ |
| 前端对话 UI | ✅ (侧边栏+消息+发送框) |
| Markdown 渲染 | ✅ |

### 2.6 文档同步情况

| 文档 | 位置 | 状态 |
|:-----|:-----|:----:|
| AI-COMPANY-OS-CONSTITUTION.md | `docs/` + 知识库 | ✅ 已新建 |
| AI-COMPANY-OS-ROADMAP.md | `docs/` + 知识库 | ✅ 已新建 |
| README.md (关系说明) | 项目根目录 | ✅ 已更新 |
| 知识库 v1.1 架构方案 | AI-Knowledge-OS | ✅ 命名已统一 |

---

## 3. 真实数据接入情况

### 3.1 数据来源对照

| 数据类型 | 当前状态 | DB 行数 | 真实源数据量 | 说明 |
|:---------|:--------:|:-------:|:------------:|:-----|
| agents | 🟡 **partial real** | 15 | 17 个 agent 目录 / 1 个 CLI 注册 | 数据来自 `~/.openclaw/agents/` 目录扫描，非 CLI 注册列表 |
| cron_jobs | 🟢 **real** | 21 | 21 | 直接读取 `~/.openclaw/cron/jobs.json`，行数精确匹配 |
| business_lines | 🟡 **partial real** | 5 | 5 条业务线（从 registry 推断） | 由 cron jobs 推导，非独立真实源 |
| execution_records | 🔴 **mock** | 30 | 14 条真实记录 | 真实 ledger schema (runIntentId/artifactId) 与 DB schema (date/business_line/result) 不匹配，同步失败 |
| artifacts | 🔴 **mock** | 5 | 文件有 JSON 解析错误 | 真实 artifact-ledger.json 格式异常，同步为 0 |
| cost_snapshots | 🟡 **partial real** | 99 | 6 agents/2 models/3 projects | 有 19 条来自真实 sync，其余为 mock；每日明细仅 1 天 (2026-03-30) |
| alerts | 🟡 **partial real** | 15 | 2 条来自 refresh | 13 条为 mock seed，2 条为 refresh 检测的真实 alert |
| refresh_log | 🟢 **real** | 4 | 4 次实际刷新 | 是真实执行记录 |

### 3.2 数据准确性摘要

| 维度 | 评估 |
|:-----|:-----|
| Agent 有 15 条，但 CLI 只注册了 1 个 (main) | ⚠️ 概念混淆：workspace 目录 vs CLI 注册 |
| Execution records 全是 mock，真实数据未同步 | 🔴 schema 不匹配，需 adapter 改造 |
| Cost data 混合真实+mock，日期陈旧 | ⚠️ 真实数据仅到 2026-03-30，且混合 mock 会误导分析 |
| Alerts 混合真实+mock | ⚠️ 用户无法区分哪些告警是真实的 |

---

## 4. 数据准确性对账

### 4.1 Agent 数量 vs `openclaw agents list`

| 数据源 | 数量 | 说明 |
|:-------|:----:|:-----|
| DB agents 表 | 15 | 包含 main + 14 个 workspace agent 目录 |
| CLI `openclaw agents list` | 1 | 仅 main (default) |
| `~/.openclaw/agents/` 目录 | 17 | 目录数量（部分可能未注册） |
| **结论** | ❌ **不一致** | DB 不从 CLI 取值，而是从 workspace 目录扫描，两者口径不同 |

### 4.2 Cron Jobs vs `~/.openclaw/cron/jobs.json`

| 数据源 | 数量 | 说明 |
|:-------|:----:|:-----|
| DB cron_jobs 表 | 21 | 含 schedule/status/error 信息 |
| `~/.openclaw/cron/jobs.json` | 21 | 真实文件 |
| **结论** | ✅ **一致** | 数量和内容匹配 |

### 4.3 Execution Records vs `production-flow-ledger.json`

| 数据源 | 数量 | 说明 |
|:-------|:----:|:-----|
| DB execution_records 表 | 30 | **全部为 mock 数据** |
| `production-flow-ledger.json` | 14 条真实运行记录 | schema 不同（runIntentId/artifactId） |
| **结论** | ❌ **完全不一致** | 真实数据未同步进入 DB |

### 4.4 Artifacts vs `artifact-ledger.json`

| 数据源 | 数量 | 说明 |
|:-------|:----:|:-----|
| DB artifacts 表 | 5 | **全部为 mock 数据** |
| `artifact-ledger.json` | ❌ 无法解析 | 文件存在但有 JSON 解析错误 |
| **结论** | ❌ **无法对账** | 真实源文件损坏或格式不标准 |

### 4.5 Costs vs Gateway-Lite

| 数据源 | 数量 | 说明 |
|:-------|:----:|:-----|
| DB cost_snapshots 表 | 99 | 含 real(19) + mock(80) 混合 |
| by-model.json | 2 models | 真实：MiniMax-M2.5 ($0.00255), deepseek-r1:8b ($0) |
| by-agent.json | 6 agents | 真实：finance-analyst, research-agent, lead-novel 等 |
| by-project.json | 3 projects | 真实项目成本聚合 |
| daily/ | 仅 1 天 | 2026-03-30 的明细数据 |
| **结论** | ⚠️ **部分一致，但混合 mock 会误导** | 用户无法区分哪些是真实成本 |

### 4.6 Alerts vs 失败/异常状态

| 数据源 | 数量 | 说明 |
|:-------|:----:|:-----|
| DB alerts 表 | 15 | real(2) + mock(13) |
| 真实 cron error | 6 errors | 亚马逊选品报告、金融投资摘要等 |
| **结论** | ⚠️ **部分一致** | 成功检测到 2 条真实 alert，但 13 条 mock 干扰了视图 |

---

## 5. 只读边界检查

### 5.1 符合 v0.1 原始范围的部分

| 约束 | 状态 | 说明 |
|:-----|:----:|:-----|
| 修改 OpenClaw runtime | ✅ 未违反 | 所有 adapter 只读不写 |
| 修改 cron jobs | ✅ 未违反 | 只读取 `jobs.json` |
| 修改 scheduler | ✅ 未违反 | 未涉及 |
| 修改 writer trigger | ✅ 未违反 | 未涉及 |
| CEO Agent 行为 | ✅ 未违反 | 未实现 CEO Agent |
| TASK-POOL 行为 | ✅ 未违反 | 未实现 TASK-POOL |

### 5.2 超出 v0.1 原始范围的部分

| 项目 | 发现 | 严重程度 |
|:-----|:-----|:--------:|
| `PATCH /api/v1/agents/{name}` | Phase 7 引入的写操作，可修改 Agent skills/role/status | ⚠️ 中 |
| `POST /api/v1/tasks` | Phase 5 创建任务，写操作 | ⚠️ 中 |
| `PATCH /api/v1/tasks/{id}` | Phase 5 更新任务状态，写操作 | ⚠️ 中 |
| `POST /api/v1/tasks/{id}/cancel` | Phase 5 取消任务，写操作 | ⚠️ 中 |
| `POST /api/v1/tasks/{id}/retry` | Phase 7 重试任务，写操作 | ⚠️ 中 |
| `POST /api/v1/command` | Phase 5 指挥台 — 向 Agent 发送指令，写操作 | 🔴 高 |
| 指挥台页面 `/command` | Phase 5 前端 — 提供写操作 UI | ⚠️ 中 |
| 任务看板 `/tasks` | Phase 6 前端 — 任务管理 UI | ⚠️ 中 |
| 分析页面 `/analysis` | Phase 7 前端 — 失败分析、缺口分析 | ✅ 只读可接受 |
| `PATCH /api/v1/agents/*` (skill/role/status) | 可修改 Agent 配置 | ⚠️ 中 |

> **总体评估**: v0.1 原始范围定义为"只读看板"，但 Phase 5/6/7 引入了写操作端点。目前的代码状态是**混合模式**——核心数据（agents/cron/runs/costs）是只读的，但新增了任务管理和指挥台功能。合规度约 **70%**。

---

## 6. Hermes 内嵌面板边界定义

### 6.1 定位

**Hermes Chat Panel** = Founder 的对话助手面板。不是 CEO Agent，不是调度系统，不是自动审批引擎。

### 6.2 它能做什么

| 能力 | 说明 |
|:-----|:------|
| ✅ 解释看板数据 | "今天的成本为什么高了？" |
| ✅ 总结趋势 | "最近 7 天哪条线最活跃？" |
| ✅ 分析问题 | "这个 Agent 为什么总失败？" |
| ✅ 头脑风暴 | "你觉得亚马逊线下一步该怎么做？" |
| ✅ 架构讨论 | "L3 和 L4 的区别是什么？" |

### 6.3 它不能做什么

| 禁止行为 | 当前是否违反 | 说明 |
|:---------|:-----------:|:-----|
| ❌ 写操作 | ✅ 未违反 | Hermes CLI 无本项目的写权限 |
| ❌ 调度 Agent | ✅ 未违反 | 未接入任何调度系统 |
| ❌ 修改 OpenClaw | ✅ 未违反 | 未连接 OpenClaw runtime |
| ❌ 创建任务/入 TASK-POOL | ✅ 未违反 | TASK-POOL 不存在 |
| ❌ 自动审批 | ✅ 未违反 | 无审批接口 |
| ❌ 调用其他 Agent | ✅ 未违反 | 无跨 Agent 调用能力 |

> **边界清晰。** Hermes Chat Panel 仅做回答和讨论，行为受限于 Hermes CLI 的权限和能力。

---

## 7. 已知问题与风险

### 🔴 高优先级

| # | 问题 | 类型 | 说明 |
|:-:|:-----|:----:|:-----|
| 1 | **Execution records 全是 mock** | 数据 | 真实生产 ledger 的 schema (runIntentId/artifactId/validatorPassed) 与 DB schema (date/business_line/result) 不匹配，adapter 无法映射，需重写或新增映射层 |
| 2 | **Artifact ledger 无法解析** | 数据 | `artifact-ledger.json` 有 JSON 格式错误，需要人工修复源文件或增加容错解析 |
| 3 | **Agent 来源口径错误** | 数据 | DB 的 agents 来自 `~/.openclaw/agents/` 目录扫描（17 个目录），而非 CLI 注册（仅 1 个 main），两种口径混用会导致用户困惑 |
| 4 | **Mock 数据污染真实视图** | 数据 | costs 表 99 条记录中仅 19 条真实；alerts 表 15 条中仅 2 条真实。用户无法区分哪些可信 |

### 🟡 中优先级

| # | 问题 | 说明 |
|:-:|:------|:------|
| 5 | **Phase 5~7 超出 v0.1 范围** | 指挥台、任务 CRUD、Agent PATCH 等写操作端点不应出现在 v0.1 中。后续需决定是回退还是重新定义 v0.1 范围 |
| 6 | **成本数据仅到 2026-03-30** | 每日明细数据非常陈旧，无法反映当前运营状态 |
| 7 | **Refresh 状态为 "partial"** | 最近 3 次 refresh 都只部分成功，execution_records 和 artifacts 返回 0 |
| 8 | **对话面板无上下文传递** | 每轮对话独立调用 Hermes CLI，无法感知当前看板状态。需要 Founder 手动描述"帮我看今天的成本" |
| 9 | **暂无外网访问** | Cloudflare tunnel 未运行，只能本地访问 |

### 🟢 低优先级

| # | 问题 | 说明 |
|:-:|:------|:------|
| 10 | 前端移动端适配不完善 | 对话面板桌面体验良好，但手机浏览器未优化 |
| 11 | 多人同时访问无状态隔离 | 当前只有一个 session 概念，多人同时操作会互相影响 |
| 12 | 无用户认证 | 任何人都可访问 localhost:3001 |

---

## 8. 下一步建议

### ✅ 默认建议：A. v0.1.1 加固真实数据与 UI

**理由**: 当前 30% 的数据是真实的，70% 是 mock。在不验证真实数据能正确展示之前，进入 v0.2 设计没有任何基础。

**建议工作项**（按优先级排序）：

| 优先级 | 工作项 | 预估天数 |
|:-----:|:-------|:--------:|
| P0 | **修复 execution_records adapter** — 将真实 ledger 的 runIntentId/artifactId schema 映射到 DB 标准字段 | 1 |
| P0 | **修复 artifact-ledger.json 解析** — 增加容错解析或人工修复源文件 | 0.5 |
| P0 | **清理 mock 数据** — 从 costs/alerts 中移除 mock 记录，仅保留真实数据 | 0.5 |
| P1 | **统一 agent 数据源** — 决定使用 CLI `openclaw agents list` 还是 workspace 目录扫描，统一口径 | 0.5 |
| P1 | **Phase 5~7 范围决策** — 回退写操作端点，或重新定义 v0.1 范围为"只读核心 + 扩展功能" | 0.5 |
| P2 | **刷新每日成本数据** — 补充近期每日成本，或连接真实 LLM 调用日志 | 0.5 |
| P2 | **对话面板感知上下文** — 自动注入当前看板状态到 Hermes 调用 | 1 |

### B. v0.2 规划 TASK-POOL + Approval Center

如果选择直接进入 v0.2，将在 mock 数据的基础上设计 TASK-POOL 和审批流程，存在以下风险：

- ⚠️ 无法验证任务流是否能正确从真实数据提取
- ⚠️ 审批面板在没有真实告警数据的情况下设计可能偏离实际需求
- ⚠️ 执行记录 adapter 未修复 → TASK-POOL 没有真实回溯数据

### 推荐

> **先走 A（v0.1.1 加固），再进 B（v0.2）。**  
> 只有当 Phase 5~7 的写操作功能被正式批准纳入 v0.1 范围后才保留，否则回退。
>
> 在验收报告签署通过前，**不新增功能，不进入 v0.2**。
