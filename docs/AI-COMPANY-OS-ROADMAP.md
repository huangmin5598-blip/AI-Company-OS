# AI Company OS 路线图

> **从 v0.1 到 v0.6+ 的分阶段演进计划**
> 每个版本都是可独立交付、可验收的里程碑。
> 长期宪法中的所有原则在后继版本中逐步落地，不在早期强行实现。

---

## 当前状态：v0.8 — Controlled Execution Bridge MVP（已完成 🏁）

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

## v0.8+ — Future Horizons

| 版本 | 核心主题 | 说明 |
|:----|:---------|:------|
| v0.7 | Controlled Self-Improvement | 系统在约束下自我改进：监控发现 → 提案 → 受控执行 |
| v0.8 | Controlled Execution Bridge | 受控执行桥 — 让提案进入可审计的一次性执行流程 |
| v0.9 | **Code-Capable Runtime Integration** | 将 Codex / Claude Code 等 Code-Capable Runtime 接入执行桥，让提案的代码修改类 action 可受控执行 |
| v1.0 | Agent Meeting Session | 多 Agent 结构化协作会议，CEO 主持 |
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
| **v0.9** | — | **Code-Capable Runtime Integration** | 🚧 |
| **v1.0** | — | Agent Meeting Session | Horizon |
| **v1.1** | — | Operating Kit Productization | Horizon |

---

## 里程碑时间线

```
v0.1 ── v0.2 ── v0.3 ── v0.4 ─ v0.5 ─ v0.6 ─ v0.7 ─ v0.8 ─ v0.9 ── v1.0 ── v1.1
可视   运 行   决 策   学 习   自我    Runtime   受控    执行桥   可编程   Agent    产品化
化     闭环    CEO    记忆     观察    注册层    改进           运行时    会议     套件
+控制

```

---

> **本文档是 AI Company OS 的产品路线图。**
> 每个版本交付前，需 Founder 确认范围、排期、验收标准。
> 版本范围变更 = 需要 Founder 批准。
