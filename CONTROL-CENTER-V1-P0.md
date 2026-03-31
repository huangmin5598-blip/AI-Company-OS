# Control Center V1 — P0 信息层框架

**版本**: 1.0
**更新时间**: 2026-03-31
**状态**: P0 - 信息层

---

## 一、信息层模块

P0 信息层至少包含以下 **7 个模块**：

| # | 模块 | 描述 | 优先级 |
|---|------|------|--------|
| 1 | Project Board | 项目状态总览 | P0 |
| 2 | Agent Status | Agent 运行状态 | P0 |
| 3 | System Health | 系统健康检查 | P0 |
| 4 | Gateway Summary | Gateway 成本与治理 | P0 |
| 5 | Capability Overview | 能力地图概览 | P0 |
| 6 | Routing Summary | 路由命中与异常 | P0 |
| 7 | CEO Escalation Summary | CEO 介入事项 | P0 |

---

## 二、数据源映射

### 模块 1: Project Board

**数据源**:
- `TASK-POOL.md` → 项目列表与状态
- `execution-records.json` → 项目产出记录
- `memory/YYYY-MM-DD.md` → 每日项目动态

**输出字段**:
| 字段 | 来源 |
|------|------|
| project_id | TASK-POOL |
| project_name | TASK-POOL |
| status | TASK-POOL (ACTIVE/ITERATION/MVP/PAUSED) |
| last_task | execution-records |
| output_count | execution-records |

---

### 模块 2: Agent Status

**数据源**:
- `openclaw agents list` → Agent 列表
- `CAPABILITY-REGISTRY.md` → Agent 能力定义
- `execution-records.json` → Agent 执行记录

**输出字段**:
| 字段 | 来源 |
|------|------|
| agent_id | openclaw |
| role | CAPABILITY-REGISTRY |
| status | openclaw (active/idle/error) |
| last_run | execution-records |
| capability | CAPABILITY-REGISTRY |

---

### 模块 3: System Health

**数据源**:
- `memory/execution-records.json` → 执行状态
- `gateway-lite/daily/*.json` → Gateway 状态
- `heartbeat.log` → 心跳状态

**输出字段**:
| 字段 | 来源 |
|------|------|
| heartbeat_status | heartbeat.log |
| gateway_status | gateway-lite |
| memory_writable | 系统检查 |
| registry_valid | execution-records |

---

### 模块 4: Gateway Summary

**数据源**:
- `gateway-lite/daily/YYYY-MM-DD.json` → 每日成本
- `gateway-lite/weekly/week-N.md` → 每周汇总

**输出字段**:
| 字段 | 来源 |
|------|------|
| total_cost | gateway-lite |
| model_usage | gateway-lite |
| fallback_count | gateway-lite |
| warning_count | gateway-lite |

---

### 模块 5: Capability Overview

**数据源**:
- `CAPABILITY-REGISTRY.md` → 能力地图

**输出字段**:
| 字段 | 来源 |
|------|------|
| core_agents_count | CAPABILITY-REGISTRY |
| system_agents_count | CAPABILITY-REGISTRY |
| active_projects_count | CAPABILITY-REGISTRY |
| boundary_count | CAPABILITY-REGISTRY |

---

### 模块 6: Routing Summary

**数据源**:
- `ROUTING-RULES.md` → 规则定义
- `execution-records.json` → 路由命中记录

**输出字段**:
| 字段 | 来源 |
|------|------|
| route_type_count | ROUTING-RULES |
| active_rules | ROUTING-RULES |
| last_route_reason | execution-records |
| escalation_count | execution-records |

---

### 模块 7: CEO Escalation Summary

**数据源**:
- `ROUTING-RULES.md` → CEO 介入条件
- `execution-records.json` → 介入记录

**输出字段**:
| 字段 | 来源 |
|------|------|
| escalation_reason | execution-records |
| last_escalation | execution-records |
| resolved_count | execution-records |
| pending_count | execution-records |

---

## 三、Daily / Weekly 输出结构

### Daily 18:00 简版

**文件名**: `REPORT-YYYY-MM-DD.md`

**结构**:
```markdown
# Daily Report — 2026-03-31

## 1. 今日项目状态
| Project | 状态 | 今日产出 |
|---------|------|----------|
| novel-v1 | ACTIVE | 2 篇 |
| research-agent | COMPLETED | 3 cards |

## 2. Agent 状态
- lead-novel: active
- writer: idle
- tiger-coder: active

## 3. Gateway 简报
- 今日成本: ¥XX
- fallback: X 次
- warning: X 次

## 4. CEO 介入事项
- [无] / [事项列表]
```

---

### Weekly 周日 20:00 完整版

**文件名**: `WEEKLY-OS-REPORT-WW-YYYY-MM-DD.md`

**结构**:
```markdown
# Weekly OS Report — Week 15, 2026-03-31

## 1. Project Board（完整）
[所有项目状态列表]

## 2. Gateway Summary
[本周成本汇总、趋势]

## 3. Capability Overview
[Agent 能力地图概览]

## 4. Routing 命中与异常
[本周路由统计、异常事件]

## 5. System Health
[Registry、Memory、Gateway 状态]

## 6. Bottleneck / Kill / Scale 建议
[基于数据的问题分析与建议]
```

---

## 四、P0 当前不做

| 不做项 | 原因 |
|--------|------|
| 实时 Web Dashboard | P0 定位是信息层，非交互产品 |
| 重交互界面 | 静态报告形式即可 |
| 大而全 Virtual Office | 后续版本考虑 |
| 新建复杂平行数据层 | 必须复用现有数据源 |
| 多租户系统 | 单用户场景不需要 |
| 复杂实时推送 | 每日/每周报告已足够 |

---

## 五、接入顺序

按以下 **最小顺序** 接入：

| 顺序 | 模块 | 预计工作量 |
|------|------|-----------|
| 1 | Project Board | 低 - 直接读 TASK-POOL |
| 2 | Agent Status | 低 - 读 openclaw + registry |
| 3 | Gateway Summary | 低 - 读 gateway-lite 数据 |
| 4 | Capability Overview | 低 - 读 CAPABILITY-REGISTRY |
| 5 | Routing Summary | 中 - 需要整理路由命中统计 |
| 6 | CEO Escalation Summary | 中 - 需要整理介入记录 |
| 7 | System Health | 中 - 需要定义检查项 |

---

## 六、与现有项目的关系

| 项目 | control-center 复用 |
|------|---------------------|
| TASK-POOL.md | ✅ Project Board 数据源 |
| execution-records.json | ✅ Agent Status, Routing Summary 数据源 |
| openclaw agents list | ✅ Agent Status 数据源 |
| heartbeat.log | ✅ System Health 数据源 |
| gateway-lite-v1 | ✅ Gateway Summary 数据源 |
| CAPABILITY-REGISTRY.md | ✅ Capability Overview 数据源 |
| ROUTING-RULES.md | ✅ Routing Summary 数据源 |

---

## 七、Registry 字段

| 字段 | 值 |
|------|-----|
| current_stage | P0 |
| next_stage | P1 |
| owner | tiger |
| end_state | 信息层完整，可展示 7 模块 |
| freeze_rule | P0 模块未完成前不冻结 |

---

## 八、next_step

1. 先实现 Project Board 模块（读取 TASK-POOL）
2. 接入 Agent Status（读取 openclaw agents + CAPABILITY-REGISTRY）
3. 接入 Gateway Summary（读取 gateway-lite 数据）
4. 后续模块逐步接入
