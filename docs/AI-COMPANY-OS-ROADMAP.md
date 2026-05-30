# AI Company OS 路线图

> **从 v0.1 到 v1.1 的分阶段演进计划**
> **每个版本都是可独立交付、可验收的里程碑。**
>
> ⚠️ **注意：本文件为旧版路线图（v0.1–v0.9.x）。**
> **最新完整路线图请参见项目根目录的 [`ROADMAP.md`](../ROADMAP.md)，涵盖 v0.1–v0.23+。**

---

## v0.8 — Controlled Execution Bridge MVP（已完成 🏁）

> **状态**: 🏁 已交付
> PRD: `docs/prd/AI-COMPANY-CONTROL-CENTER-v0.8-CONTROLLED-EXECUTION-BRIDGE-MVP-PRD.md`
> Tags: `v0.8-sprint-a`, `v0.8-sprint-b`, `v0.8`
> Release: [v0.8](https://github.com/huangmin5598-blip/AI-Company-OS/releases/tag/v0.8)

**目标：** 让 v0.7 批准的 Improvement Proposal 进入**一次性、可审计、可验证**的受控执行流程。

### 五个执行原则

| 原则 | 含义 |
|:-----|:------|
| One-shot only | 没有自动重试、自动修复循环 |
| Founder confirmation | 必须先确认（执行人 = founder） |
| Dry-run first | 命令型动作必须先预览 |
| No destructive action | 不支持 delete/deploy/restart |
| Verification required | 执行后必须验证 |

### 交付能力

| Sprint | 内容 | 关键文件 |
|:-------|:-----|:---------|
| A | Backend — Model, Router, Policy, Dry-run, Executor, Verification | `execution_request.py`, `execution_bridge/`, `execution_requests.py` |
| B | Frontend — List page, Detail page, State machine UI, Navigation | `execution-requests/page.tsx`, `[...]/[id]/page.tsx` |

### 验收

- ✅ 5 种 Safe Action 白名单（diagnose_task / create_retry_task / generate_memory_update_draft / run_status_check / run_dry_run_command）
- ✅ 严格状态机：pending_confirmation → (dry_run_completed →) approved_for_execute → executed → verified_success/verified_failed
- ✅ Blocked action 拦截 + 审计日志（ceo_action_logs）
- ✅ Duplicate 防护：已批准 proposal 跳过，提案状态锁闭
- ✅ Dry-run 只生成文本预览，不执行 shell
- ✅ create_retry_task 不 cancel/restart 原任务
- ✅ Learning Candidate 去重（每 execution_request 最多 1 条）
- ✅ Proposal 状态自动同步（closed_success / closed_failed）
- ✅ 前端执行桥：列表 + 详情 + 步骤指示器 + 操作按钮
- ✅ Founder override 已删除
- ✅ v0.8 前端 build 0 error
- ✅ 8 个端点全链路测试通过
- ✅ Git tag + GitHub Release

---

## v0.9 — Code-Capable Runtime Bridge MVP（已完成 🏁）

> **状态**: 🏁 已交付
> PRD: `docs/prd/AI-COMPANY-CONTROL-CENTER-v0.9-CODE-CAPABLE-RUNTIME-BRIDGE-MVP-PRD.md`
> Tags: `v0.9-sprint-a0-a`, `v0.9-sprint-b`, `v0.9-sprint-c`
> Release: [v0.9](https://github.com/huangmin5598-blip/AI-Company-OS/releases/tag/v0.9)

**目标：** 将 Codex / Claude Code 等 Code-Capable Runtime 接入 AI Company OS 的受控执行桥，让非技术 Founder 可以安全地指挥 Coding Agent 改代码，不审 diff，只看摘要。

**Goal:** Integrate Code-Capable Runtimes (Codex, Claude Code) into the Controlled Execution Bridge — so non-technical founders can safely direct coding agents to make changes, reviewing natural-language summaries instead of code diffs.

### 四条安全原则 / Four Safety Principles

1. **No direct main editing** — all patches go to `.ai-company-os/staging/{id}/`, apply is local workspace only
2. **No automatic deploy** — apply is workspace-only; commit/push/deploy are manual
3. **Protected files hard block** — 14 patterns pre-check + post-check (.env, .db, secrets, credentials, deploy config, DB migrations, etc.)
4. **Every step requires confirmation** — plan approval, patch generation, checks review, apply/rollback decision

### 交付能力 / Deliverables

| Sprint | 内容 / Content | 关键文件 / Key Files |
|:-------|:---------------|:---------------------|
| A0+A | **Code-Capable Runtime Adapter** — abstract base + Codex real adapter + mock adapter + Claude Code experimental shape + factory | `runtime/code_capable/` |
| B | **Backend Core Flow** — code_change_request model (10 states), code_bridge pipeline (planner, patch generator, checks runner, applier, rollback), full REST API | `code_bridge/`, `models/code_change_request.py`, `routers/code_change_requests.py` |
| C | **Frontend Founder UI** — list page with status filters & summary cards, detail page with diff viewer, check result cards, protected file warnings, confirmation modals, state machine steps | `code-change-requests/page.tsx`, `[id]/page.tsx` |

### API Endpoints

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

### State Machine

```
draft → plan_generated → plan_approved → patch_generated
  → checks_passed / checks_warning / checks_failed
    → applied → rolled_back
    → rejected / revised back to plan_approved
```

### 验收 / Verification

- ✅ Code-Capable Runtime abstract + Codex real adapter + mock adapter
- ✅ Full state machine (10 states, 7 transitions)
- ✅ Staging in `.ai-company-os/staging/` with isolated check_workspace
- ✅ Protected file double-check (pre-check + post-check)
- ✅ `safe_path_join()` — no path traversal, repo escape, .git escape
- ✅ Apply → `verification_pending` → founder verifies
- ✅ One-click rollback
- ✅ 3-spawn backend + frontend both live
- ✅ Frontend list page + detail page + confirmation modals
- ✅ 978 lines of new backend code, 968 lines of new frontend code

---

## v0.4.1 — Productization & Runtime Readiness

**目标：** 为产品化做架构垫片。将 OS Core 与公司特定配置分离，定义 Runtime Adapter Protocol，建立产品化标记体系。

### 交付物

| 交付物 | 说明 |
|:-------|:------|
| 产品化架构文档 | 四层架构：OS Core / Company Instance / Operating Kit / Evidence Layer |
| RuntimeAdapter Protocol | 统一 Actor 抽象层接口定义 |
| Company Instance Config | 配置样板，分离 Core vs Config |
| 产品化标记 | 扫描代码，标记 Product/Platform/Internal |
| Monitor Framework 架构预览 | v0.5 前瞻设计 |

### 预估工时

4-6h（轻量插入 sprint）

### 不做

多租户 · 权限系统 · 云部署 · 计费 · 模板市场 · 完整多 Runtime · Paperclip 集成

---

## v0.5 — Monitor Framework Lite

**目标：** 系统开始自我观察并提出改进建议。按 probes / analyzers / outputs / config 四层架构，面向 RuntimeAdapter Protocol 实现。

### 核心能力

| 模块 | 说明 |
|:-----|:------|
| Probes | 数据采集层：hermes_probe（Hermes 状态）、openclaw_probe（OpenClaw 状态） |
| Analyzers | 分析层：检测告警、异常、效率下降、记忆空洞 |
| Config | 用户可配置：检查周期、触发阈值、输出通道 |
| Outputs | 输出层：写告警 → Alert → Company Loop 闭环 |

### 不做

自动修复 · 自动写知识库 · 跨 Runtime 聚合

---

## v0.6 — Runtime Layer MVP 🏁

> **状态**: 🏁 已交付
> PRD: `docs/prd/AI-COMPANY-CONTROL-CENTER-v0.6-RUNTIME-LAYER-MVP-PRD.md`
> Tag: `v0.6-sprint-c`

**目标：** 让系统知道"自己有哪些身体器官" — 将 RuntimeAdapter Protocol 落地为真实运行时注册与健康检查层。

### 交付能力

| Sprint | 内容 | 文件变更 |
|:-------|:-----|:---------|
| A | Core Runtime Layer | +8 文件 / +605 行 — Models, Adapters (Hermes/OpenClaw/Codex/ClaudeCode), Registry, Router, Seed |
| B | Monitor Integration | runner 修复 + 配置文件更新 — runtime_health finding 离线检测 |
| C | Frontend Grouping | Agents 页面按 Runtime 分组，保留原 Agent Card 完整不变 |

### 验收

- ✅ 4 个 Runtime 注册：Hermes Agent (online) / OpenClaw Gateway (online) / Codex (placeholder, enabled=0) / Claude Code (placeholder, enabled=0)
- ✅ Runtime 离线 → runtime_health [critical] finding + alert 自动生成
- ✅ Codex/Claude Code placeholder (enabled=0) 不产生 Monitor 噪音
- ✅ GPT 9 点全修复（工厂方法、枚举统一、幂等 seed、只读边界、etc.）

---

## v0.9.2 — External Runtime Connector MVP（已完成 🏁）

> **状态**: 🏁 已交付（2026-05-17）
> PRD: `docs/prd/AI-COMPANY-CONTROL-CENTER-v0.9.2-EXTERNAL-RUNTIME-CONNECTOR-MVP-PRD.md`
> Execution Plan: `docs/prd/...v0.9.2-...EXTERNAL-RUNTIME-CONNECTOR-MVP-EXECUTION-PLAN.md`
> Tags: `v0.9.2`
> Release: [v0.9.2](https://github.com/huangmin5598-blip/AI-Company-OS/releases/tag/v0.9.2)

**目标：** 将 AI Company OS 从仅支持本地 Codex 扩展为**统一 Runtime 接入框架**，支持本地 Agent、实验性 Agent、云端 Agent 的注册与选择。

### 交付能力

| Sprint | 内容 | 关键文件 |
|:-------|:-----|:---------|
| 1 | **External HTTP Agent Adapter** — 通用远程 Agent 模板，含 endpoint_url 白名单校验、auth 仅环境变量、execute() 硬禁用 | `adapters/external_http_adapter.py` |
| 2 | **Claude Code Spike** — 真实 health_check + capability + generate_plan（25s），generate_patch/apply 被 experimental 阻塞 | `adapters/claude_code_stub.py`, `code_capable/claude_adapter.py` |
| 3 | **Runtime 端点配置** — 3 个 disabled cloud runtime 注册（cloud-openclaw, cloud-hermes, minimax-agent） | `db/seed_runtimes.py` |
| 4 | **CCR runtime_id 参数 + 安全边界** — 所有 CCR 端点接收 runtime_id，6 条安全边界到位 | `routers/code_change_requests.py` |

### 验收

- ✅ 3 个本地 Runtime：Hermes / OpenClaw / Codex
- ✅ 1 个实验性 Runtime：Claude Code（generate_plan 25s，patch/apply 拒绝）
- ✅ 3 个云端 disabled slot：cloud-openclaw / cloud-hermes / minimax-agent
- ✅ external execute() 硬禁用，返回 unsupported
- ✅ auth 仅走环境变量，不进 config/git
- ✅ endpoint_url 安全白名单（禁止 file/ftp/metadata IP）
- ✅ disabled runtime 不通健康检查，零触达远程
- ✅ CCR runtime_id 默认 codex，不存在或 disabled 返回 422
- ✅ Claude Code 升级 v2.1.47 → v2.1.150 后 generate_plan 可用
- ✅ ACP 非 TTY 阻塞原因已记录为 skill
- ✅ 前后端均无改动，仅后端扩展

---

## v0.9+ — Future Horizons

| 版本 | 核心主题 | 说明 |
|:----|:---------|:------|
| v0.9.3 | **Scheduled Research-to-Opportunity MVP** | 每周固定研究的 Research Agent 工作线，生成 Weekly Brief + Opportunity Cards + Opportunity Pool |
| v1.0 | **Agent Meeting Session** | 多 Agent 结构化协作会议，CEO 主持 |
| v1.1 | Operating Kit Productization | Operating Kit 作为独立产品层可售 |

---

## 版本演进总览

| 版本 | 日期 | 核心主题 | 状态 |
|:----|:----:|:---------|:----:|
| **v0.1.x** | 2026-05-21 | Visibility + Control | 🏁 |
| **v0.2** | 2026-05-23 | **Company Loop MVP** | 🏁 |
| **v0.3** | 2026-05-23 | CEO Agent Lite | 🏁 |
| **v0.4** | 2026-05-23 | **Company Memory MVP** | 🏁 |
| **v0.4.1** | 2026-05-24 | **Productization & Runtime Readiness** | 🏁 |
| **v0.5** | 2026-05-23 | **Monitor Framework Lite** | 🏁 |
| **v0.6** | 2026-05-24 | **Runtime Layer MVP** | 🏁 |
| **v0.7** | 2026-05-24 | **Controlled Self-Improvement** | 🏁 |
| **v0.8** | 2026-05-17 | **Controlled Execution Bridge** | 🏁 |
| **v0.9** | 2026-05-24 | **Code-Capable Runtime Integration** | 🏁 |
| **v0.9.1** | 2026-05-25 | **Schema Patch Integration** | 🏁 |
| **v0.9.2** | 2026-05-17 | **External Runtime Connector MVP** | 🏁 |
| **v0.22.1** | 2026-05-30 | **Decision-to-Execution Result Backfill** | 🏁 已完成 |
| **v0.23** | 2026-05-30 | **Run Ledger MVP + Asset Registry MVP** | 🏁 已完成 |
| **v0.24** | 2026-05-30 | **CEO Command Interface + Capability Registry P0** | 🏁 已完成 |
| **v0.25** | 2026-05-30 | **Founder Control Plane — 5-Tab IA + Founder Console + Preflight 11/11** | 🏁 已完成 |
| **v0.26** | 2026-05-30 | **Evidence Dashboard Lite + GitHub Refresh** | 🏗️ 进行中 |
| **v0.27** | — | **Operating Kit v0.1 + Capability Boundary** | 🔮 计划中 |
| **v0.28** | — | **Company Instance Config + Runtime Manifest** | 🔮 计划中 |
| **v0.29** | — | **Workflow Composition** | 🔮 计划中 |
| **v1.0** | — | **Product Launch / Operating Kit Productization** | Horizon |
| **─** | — | *Agent Meeting 已删除，替换为 v0.29 Workflow Composition* | — |

---

## 里程碑时间线

```
v0.1 ── v0.2 ── v0.3 ── v0.4 ─ v0.5 ─ v0.6 ─ v0.7 ─ v0.8 ─ v0.9 ─ v0.9.2 ── v0.13─v0.17 ── v0.18─v0.23 ── v0.24─v0.29 ── v1.0
|可视   运 行   决 策   学 习   自我    Runtime   受控    执行桥   可编程  统一      Agent     决策→执行     系统级能力        Product
|化     闭环    CEO    记忆     观察    注册层    改进           运行时   Runtime    真实执行   闭环      建设         Launch

```

---

> **本文档是 AI Company OS 的产品路线图。**
> 每个版本交付前，需 Founder 确认范围、排期、验收标准。
> 版本范围变更 = 需要 Founder 批准。
