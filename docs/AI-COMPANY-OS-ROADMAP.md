# AI Company OS 路线图

> **从 v0.1 到 v0.6 的分阶段演进计划**
> 每个版本都是可独立交付、可验收的里程碑。
> 长期宪法中的所有原则在后继版本中逐步落地，不在 v0.1 强行实现。

---

## 当前状态：v0.2 — Company Loop MVP（已完成 🏁 2026-05-22）

> **状态**: 🏁 已交付 · 2026-05-22
>
> 见 `docs/prd/AI-COMPANY-CONTROL-CENTER-v0.2-COMPANY-LOOP-MVP-PRD.md`
> 验收标准：一条真实告警完整走通闭环。

**目标：** 将 Control Center 从"可视化层"升级为 AI Company OS 的第一个"公司运行闭环"。

### 核心链路

```
Alert / Command / Manual Input → Task → Context Pack → Approval → Execute → Review → Learning Candidate
```

### 范围速览

| 模块 | 说明 |
|:-----|:------|
| TASK-POOL | 唯一任务源/意图寄存器，升级现有 tasks 表 |
| Context Pack | 每个任务绑定的最小公司上下文（含知识库引用） |
| Approval Center | Founder 自确认/决策留痕，不是企业审批流 |
| Review Gate | PASS / REVISION REQUIRED / BLOCKED 三态验收 |
| Learning Candidate | 失败/经验/规则/工具缺口的自我改进入口 |
| Alert 自动入池 | 已有告警 → 自动生成 Task + Context Pack → 入审批 |
| 冷启动迁移 | alerts / command_logs / execution_records → 首批数据 |

### 验收标准

一条真实告警完整走完：Alert → Task → Context Pack → Approval → Execute → Review → Learning Candidate

### 不做

CEO Agent · 完整 Monitor Agent · Agent Meeting · 多 Runtime · 自动修复 · 自动写知识库 · Tool Registry · Event Trace 新表

### 数据层

5 张新表：`task_pool` · `context_packs` · `approvals` · `reviews` · `learning_candidates`

### 预估工时

14-18h（约 2-3 天冲刺）

---

## v0.3 — CEO Agent Lite

**目标：** CEO Agent 作为 Founder 的唯一对话接口上线，实现基本调度能力。

### 核心能力

| 模块 | 说明 |
|:-----|:------|
| CEO Agent | 1 个 Hermes 实例，不自执行，只做调度 |
| Founder 接口 | 飞书 + CC 对话面板双通道 |
| 目标拆解 | Founder 说目标 → CEO 拆成可执行任务 → 入 TASK-POOL |
| 任务分派 | CEO 将任务派给对应 Project Lead / Execution Agent |
| 低风险代批 | 按规则引擎自动批准已知安全的小决策 |
| 汇总汇报 | 每日/按需产出系统运行简报 |

### 不可变

- CEO Agent 不自执行具体任务
- Monitor Agent 仍未上线

---

## v0.3 — CEO Agent Lite / Founder Intent Interface（已完成 🏁 2026-05-22）

> **状态**: 🏁 已交付 · 2026-05-22
>
> 见 `docs/prd/AI-COMPANY-CONTROL-CENTER-v0.3-CEO-AGENT-LITE-PRD.md`
> 执行计划见 `docs/prd/AI-COMPANY-CONTROL-CENTER-v0.3-CEO-AGENT-LITE-EXECUTION-PLAN.md`

**目标：** Founder 可以通过自然语言向 AI Company OS 表达目标和确认审批，CEO Agent 负责理解意图、调后端写入 TASK-POOL/Approval Center，但不自动执行、不自动审批。

### 核心链路

```
Goal Intake:    Founder Goal → CEO Agent → Task Proposal → Context Pack → Approval Center
Approval Action: Founder "批准" → CEO Agent → Approval API → 留痕
```

### 范围速览

| 模块 | 说明 |
|:-----|:------|
| CEO Skill（Hermes） | 目标拆解 + 审批操作解析，结构化 schema 输出 |
| goal_sessions | Founder 输入目标的完整记录 |
| ceo_action_logs | 所有 CEO 代操作的审计日志 |
| commit-decomposition | 原子写入：goal → tasks → context_packs → approvals → logs |
| CC Panel 输入入口 | CEO Console 页面 |

### 不做

自动执行 · 自动分派 · 低风险代批 · Status Query NL · Monitor Agent · Agent Meeting · 多 Runtime

### 验收标准

1. Goal Intake: 目标 → 2-5 个 task + Context Pack + Approval ✅
2. Approval Action: "批准 task X" → 唯一匹配 → 执行 → 留痕 ✅

---

## v0.4 — Company Memory MVP（已完成 🏁）

> **状态**: 🏁 **已完成** · 2026-05-17
> PRD: `docs/prd/AI-COMPANY-CONTROL-CENTER-v0.4-COMPANY-MEMORY-MVP-PRD.md`
> 执行计划: `docs/prd/AI-COMPANY-CONTROL-CENTER-v0.4-COMPANY-MEMORY-MVP-EXECUTION-PLAN.md`

**目标：** 把已批准的 Learning Candidate 转化为可被 CEO Agent 召回的组织记忆（org_memory），建立 Knowledge Pipeline。

### 核心链路

```
Learning Candidate approved
  → Knowledge Proposal (draft)  ← Founder 手动确认
    → Commit to org_memory (FTS5)
      → CEO Agent Goal Intake 前 /memory/recall → Context Pack.referenced_memory_ids
```

### 关键设计

| 模块 | 说明 |
|:-----|:------|
| org_memory 表 | 5 种 memory_type + FTS5 全文搜索 + 来源链（candidate/review/task/goal_session） |
| knowledge_proposals | 半自动生成，Founder 确认后才 commit，committed 状态防重复 |
| /memory/recall | 中文友好的 FTS5 top 3 召回，CEO Agent Goal Intake 前自动调用 |
| FTS5 capability check | 不可用时降级 LIKE，系统不崩溃 |
| Context Pack | 独立 referenced_memory_ids 字段，不复用 referenced_knowledge |

### 不做

Monitor Agent · 自动修复 · 自动写 AI-Knowledge-OS · 向量库 · Agent Meeting · 多 Runtime

---

## v0.5 — Agent Meeting Session

**目标：** 实现 Agent 间结构化协作会议，支持多 Agent 同步工作和群聊模式。

### 核心能力

| 模块 | 说明 |
|:-----|:------|
| Agent Meeting | CEO 主持，多个 Project Lead/Exec 参会 |
| Session 管理 | 创建/加入/记录/回放 Agent 会议 |
| 群聊模式 | 多个 Agent 在共享上下文中协作 |
| 决策留痕 | 每次会议产出一份结构化决策记录，沉淀进 L3 组织记忆 |
| 争议仲裁 | CEO Agent 负责仲裁 Agent 之间的分歧 |

### 不可变

- Agent 之间仍禁止直接调用 — 所有交互通过会议 session 由 CEO 主持
- 群聊记录自动归入组织记忆，不丢失

---

## v0.6 — 多 Runtime 接入

**目标：** 支持多种 Runtime（Hermes / Codex / Claude Code / 云端推理）统一接入 AI Company OS。

### 核心能力

| 模块 | 说明 |
|:-----|:------|
| Runtime Adapter | 统一的 Actor 抽象层，每种 Runtime 几十行代码 |
| ACP 协议 | Codex / Claude Code 接入编程线 |
| MCP 协议 | 外部工具库统一接入 |
| 成本聚合 | 跨 Runtime 的 Token 消耗统一统计 |
| 能力发现 | 自动检测各 Runtime 支持的 Skill/工具集 |

### 不可变

- 更换 Runtime 不影响 OS 口径、命名规则、宪法原则
- 所有 Runtime 行为受 AI Company OS 协议约束

---

## 版本演进总览

| 版本 | 日期 | 核心主题 | 状态 |
|:-----|:----:|:---------|:----:|
| **v0.1.x** | 2026-05-21 | 可视化 + 控制层（数据可信/安全边界/解释能力） | 🏁 完成 |
| **v0.2** | 2026-05-22 | **Company Loop MVP**（闭环运行层） | 🏁 完成 |
| **v0.3** | 2026-05-22 | CEO Agent Lite / Founder Intent Interface | 🏁 完成 |
|| **v0.4** | 2026-05-17 | **Company Memory MVP**（Knowledge Pipeline） | 🏁 完成 |
| **v0.4.1** | — | Knowledge OS Bridge | 🔮 待排期 |
| **v0.5** | — | Monitor Agent Lite | 🔮 待排期 |
| **v0.6** | — | Controlled Self-Improvement | 🔮 待排期 |
| **v0.7** | — | Multi-Runtime Layer | 🔮 待排期 |
| **v0.8** | — | Agent Meeting Session | 🔮 待排期 |
| **v0.9** | — | Operating Kit Productization | 🔮 待排期 |

---

## 里程碑时间线

```
v0.1.x ── v0.2 ── v0.3 ── v0.4 ── v0.5 ────── v0.6 ─────── v0.7 ────── v0.8
可视化   运 行   决 策   学 习   自我改进    多 Runtime    Agent 会议   产品化
+控制    闭环    CEO    Monitor             接入
```

---

> **本文档是 AI Company OS 的产品路线图。**
> 每个版本交付前，需 Founder 确认范围、排期、验收标准。
> 版本范围变更 = 需要 Founder 批准。
