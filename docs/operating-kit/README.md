---
title: "Operating Kit v0.1 — AI Company OS 运营套件"
domain: operating-kit
---

# Operating Kit v0.1 — AI Company OS 运营套件

> **版本**：v0.1 · 2026-05-17  
> **用途**：将 AI Company OS 已跑通的运营流程沉淀为可复用方法论  
> **前提**：系统已完整安装并配置（详见 Evidence Dashboard）

---

## 什么是 Operating Kit？

Operating Kit 是 AI Company OS 运营方法论的**可复用文档集合**。它不是产品说明书，而是系统在真实运营中积累的流程、状态机、角色分工和运行原则。

每一份文档都来自**真实系统运行数据**——不是空泛的方法论。

---

## 文档目录

| # | 文档 | 内容 | 对应版本 |
|:--|:-----|:------|:---------|
| 1 | [DAILY-OPERATING-LOOP.md](DAILY-OPERATING-LOOP.md) | 每日运营循环：launchd 触发 → 调度 → 执行 → Brief | v0.17 |
| 2 | [DECISION-TO-EXECUTION.md](DECISION-TO-EXECUTION.md) | 决策到执行链路：Review → Decision → Draft → WO → Execute | v0.18–v0.22 |
| 3 | [WORK-ORDER-LIFECYCLE.md](WORK-ORDER-LIFECYCLE.md) | 工单状态机：创建 → 路由 → 执行 → 完成 | v0.10–v0.22 |

---

## 系统架构概览

```
┌────────────────────────────────────────────────────┐
│                  Founder Control Plane              │
│  ┌─────────┐ ┌──────────┐ ┌──────────────────────┐ │
│  │ CEO Cmd │ │  Console │ │  Evidence Dashboard  │ │
│  └────┬────┘ └────┬─────┘ └──────────┬───────────┘ │
├───────┴───────────┴──────────────────┴────────────┤
│              Governance Kernel                     │
│  ┌───────────────┐ ┌─────────────────────────┐    │
│  │ Skill Registry│ │  Capability Boundary    │    │
│  │ Routing       │ │  (5 类动作规则)          │    │
│  └───────┬───────┘ └──────────┬──────────────┘    │
├──────────┴────────────────────┴───────────────────┤
│              Execution Spine                       │
│  ┌─────────┐ ┌──────────┐ ┌─────────────────────┐ │
│  │Operating│ │Work Order│ │  Executor (sync/    │ │
│  │  Loop   │ │  Control │ │  async/remote)      │ │
│  └─────────┘ └──────────┘ └─────────────────────┘ │
├───────────────────────────────────────────────────┤
│           Memory & Asset Layer                     │
│  ┌──────────┐ ┌──────────────┐ ┌────────────────┐ │
│  │Run Ledger│ │Asset Registry│ │  Cost Summary  │ │
│  └──────────┘ └──────────────┘ └────────────────┘ │
└───────────────────────────────────────────────────┘
```

---

## 核心原则

1. **默认只读** — 查询操作无需审批
2. **安全输出** — 报告生成自动 sanitize，不泄露敏感数据
3. **审批写入** — 写入操作（WO 创建/执行）需 Founder 确认
4. **危险禁止** — 删除资产、绕过审批、暴露敏感数据直接禁止

详见 [Capability Boundary](../governance/CAPABILITY-BOUNDARY.md)。

---

## 运行状态（当前）

| 指标 | 数值 | 来源 |
|:-----|:------|:------|
| Work Orders | 433 条 | asset_registry |
| Run Ledger 事件 | 78 条 | run_ledger_events |
| 资产登记 | 4+ 个类型 | asset_registry |
| 健康检查 | 11/11 pass | Preflight |
| 测试基线 | 21/21 pass | pytest |

---

## 快速参考

| 操作 | 命令 |
|:-----|:------|
| 运行每日循环 | `python3 scripts/run_operating_loop.py --once` |
| 审批 WO | `python3 scripts/work_order_control.py approve-dispatch <WO_ID>` |
| 等待执行结果 | `python3 scripts/work_order_control.py wait-result <WO_ID>` |
| 查看最近事件 | `python3 scripts/os_registry.py ledger recent` |
| 列出资产 | `python3 scripts/os_registry.py assets list` |
| 查看资产链路 | `python3 scripts/os_registry.py lineage <asset_id>` |
| 生成证据摘要 | `python3 scripts/ceo_cmd.py evidence generate` |
| 创建 CEO Brief | `python3 scripts/run_operating_loop.py --dry-run` |

---

## 限制（v0.1）

- Operating Kit 当前为纯文档形态，非集成式交互指南
- 不含销售文档或商业化的定价/许可条款
- 部分流程（如 Founder Review）依赖手动 CLI，无 Web UI
- Capability Boundary 为 advisory mode，未自动拦截
