# AI Company OS 路线图

> **从 v0.1 到 v0.6+ 的分阶段演进计划**
> 每个版本都是可独立交付、可验收的里程碑。
> 长期宪法中的所有原则在后继版本中逐步落地，不在早期强行实现。

---

## 当前状态：v0.4 — Company Memory MVP（已完成 🏁）

> **状态**: 🏁 已交付
> PRD: `docs/prd/AI-COMPANY-CONTROL-CENTER-v0.4-COMPANY-MEMORY-MVP-PRD.md`
> 验收：5 条验收全部通过

**目标：** 把已批准的 Learning Candidate 转化为可被 CEO Agent 召回的组织记忆（org_memory），建立 Knowledge Pipeline。

### 核心链路

```
Learning Candidate approved
  → Knowledge Proposal (draft)  ← Founder 确认
    → Commit to org_memory (FTS5)
      → CEO Agent Goal Intake 前 /memory/recall → Context Pack.referenced_memory_ids
```

### 已交付能力

- OrgMemory 表 — 22 列、5 种 memory_type、FTS5 全文搜索 + 来源链
- Knowledge Proposals — 半自动生成，Founder 确认后 commit，committed 状态防重复
- Memory Search — FTS5 优先，中文自动降级 LIKE，系统不崩溃
- Memory Recall — CEO Agent Goal Intake 前自动调用，空结果不阻断
- CEO Skill 增强 — Goal Intake 前自动 /memory/recall

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

## v0.6 — Multi-Runtime Layer

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

## v0.7+ — Future Horizons

| 版本 | 核心主题 | 说明 |
|:----|:---------|:------|
| v0.7 | Controlled Self-Improvement | 系统在约束下自我改进：自动修复、技能迭代、规则优化 |
| v0.8 | Agent Meeting Session | 多 Agent 结构化协作会议，CEO 主持 |
| v0.9 | Operating Kit Productization | Operating Kit 作为独立产品层可售 |

---

## 版本演进总览

| 版本 | 日期 | 核心主题 | 状态 |
|:----|:----:|:---------|:----:|
| **v0.1.x** | 2026-05-21 | Visibility + Control | 🏁 |
| **v0.2** | 2026-05-23 | **Company Loop MVP** | 🏁 |
| **v0.3** | 2026-05-23 | CEO Agent Lite | 🏁 |
| **v0.4** | 2026-05-23 | **Company Memory MVP** | 🏁 |
| **v0.4.1** | — | **Productization & Runtime Readiness** | 🚧 |
| **v0.5** | 2026-05-23 | **Monitor Framework Lite** | 🏁 |
| **v0.6** | — | **Runtime Layer MVP** | 🚧 |
| **v0.7** | — | Controlled Self-Improvement | Planned |
| **v0.8** | — | Codex / Claude Code Repair Workflow | Horizon |
| **v0.9** | — | Agent Meeting Session | Horizon |

---

## 里程碑时间线

```
v0.1.x ── v0.2 ── v0.3 ── v0.4 ── v0.4.1 ── v0.5 ── v0.6 ── v0.7 ── v0.8 ── v0.9
可视     运 行   决 策   学 习   产品化   自我    多    受控    Agent   产品化
化     闭环    CEO    记忆    准备     观察   Runtime  改进    会议    套件
+控制                                      接入
```

---

> **本文档是 AI Company OS 的产品路线图。**
> 每个版本交付前，需 Founder 确认范围、排期、验收标准。
> 版本范围变更 = 需要 Founder 批准。
