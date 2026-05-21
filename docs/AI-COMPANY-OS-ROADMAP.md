# AI Company OS 路线图

> **从 v0.1 到 v0.6 的分阶段演进计划**
> 每个版本都是可独立交付、可验收的里程碑。
> 长期宪法中的所有原则在后继版本中逐步落地，不在 v0.1 强行实现。

---

## 当前状态：v0.1.1 — Control Center 稳定化

> 🏁 **v0.1.1 已完成**（2026-05-21）  
> Tags: `v0.1.1-p0` | `v0.1.1`

**目标：** 在 v0.1 功能骨架基础上，加固数据可信化与安全边界，不新增功能。

### 完成内容

| 模块 | 内容 |
|:-----|:-----|
| ✅ P0: Mock 数据隔离 | 5 张表加 `data_source` 字段，API 默认过滤 mock |
| ✅ P0: 真实数据刷新 | 14 条真实执行记录，19 条真实成本，6 条真实告警 |
| ✅ P0: Command dry-run 默认 | 所有写操作默认 dry-run，不执行 |
| ✅ P1: Agent 三维状态 | discovery / activity / health 独立判定 + 前端 3D Badge |
| ✅ P1: 写操作三重门禁 | dry-run + `ALLOW_ALPHA_WRITE` + `X-Confirm` |
| ✅ P1: command_logs 全覆盖 | 所有写操作记录审计日志 |
| ✅ P1: 前端 Alpha 标识 | Command Center + Chat Panel 标注 Alpha |
| ✅ 截图证据归档 | 4 张关键页面截图存于 `docs/assets/screenshots/` |
| ✅ Release Notes | `docs/releases/AI-COMPANY-CONTROL-CENTER-v0.1.1.md` |
| ✅ Build Log | `docs/build-logs/2026-05-21-control-center-v0.1.1.md` |

### 关键指标

| 指标 | 值 |
|:-----|:----|
| Agent 总数 | 18（15 online / 3 offline） |
| 真实执行记录 | 14 条（100% passed） |
| 真实成本条目 | 19 条（6 Agents, $0.0102 累计） |
| 未解决告警 | 6 条（自动检测） |
| Cron Jobs | 21 个（100% 真实） |

### v0.1.2 / P2-lite 候选（未排期）

| 工作项 | 优先级 |
|:-------|:------:|
| 成本数据同步修复（补充近期每日成本） | P2 |
| Hermes Chat Panel 上下文感知 | P2 |
| artifact-ledger 解析修复 | P2 |

---

## v0.2 — TASK-POOL + Approval Center

**目标：** 引入统一任务池和审批中心，建立任务驱动的协作基础。

### 核心能力

| 模块 | 说明 |
|:-----|:------|
| TASK-POOL | 统一的"唯一任务源"，所有任务显式注册 |
| Approval Center | 审批面板：Monitor 建议 / 跨线变更 / 新 Agent 上线 |
| 状态管理 | 待执行 / 进行中 / 已完成 / 失败 / 已取消 |
| 执行模式 | standard / lite / resume / blocked / skipped 自动选择 |
| 基础 Review 流程 | Project Lead 验收三态门禁（PASS / REVISION / BLOCKED） |

### 不可变

- 写入操作仅限于 TASK-POOL 和 Approval Center
- CEO Agent 仍未上线（人工调度仍由 Founder 通过面板操作）

---

## v0.3 — CEO Agent

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

## v0.4 — Memory / Asset Layer

**目标：** 实现 Memory 4 层架构，建立组织记忆和资产沉淀。

### 核心能力

| 层 | 实现 | 说明 |
|:---|:-----|:------|
| L1 执行记录 | SQLite（已有） | 所有任务原始数据，自动记录 |
| L2 域记忆 | 各 Hermes 实例自有 | 角色设定、风格指南、连载进度等 |
| L3 组织记忆 | SQLite FTS5 | 成功模式/失败案例/Agent 能力档案/产品记忆 |
| L4 知识库 | AI-Knowledge-OS | 最佳实践/SOP/方法论/协议文档 |
| Monitor Agent | Hermes | 跨域只读 → 分析 → 提建议 → 入审批队列 |

### 不可变

- Monitor 只建议，不执行，不调度
- 所有记忆层只追加，不覆写（保留历史版本）

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
| **v0.1** | 2026-05-21 | Control Center 功能骨架 | 🏁 完成 |
| **v0.1.1** | 2026-05-21 | 数据可信化 + 安全边界 | 🏁 **完成** |
| v0.2 | — | TASK-POOL + Approval Center | 📋 待排期 |
| v0.3 | — | CEO Agent | 🚧 待排期 |
| v0.4 | — | Memory 4 层 + Monitor Agent | 🔮 待排期 |
| v0.5 | — | Agent Meeting Session | 🔮 待排期 |
| v0.6 | — | 多 Runtime 接入 | 🔮 待排期 |

---

## 里程碑时间线

```
v0.1 ── v0.1.1 ── v0.2 ─────── v0.3 ─────── v0.4 ─────── v0.5 ─────── v0.6
骨  架   稳  定   任务池+审批   CEO Agent    Memory 4层   Agent 会议   多 Runtime
                                                        + Monitor
                                                        上线
```

---

> **本文档是 AI Company OS 的产品路线图。**
> 每个版本交付前，需 Founder 确认范围、排期、验收标准。
> 版本范围变更 = 需要 Founder 批准。
