# Run Ledger / Event Bus v1

**Project**: run-ledger-v1
**Version**: 1.0 (v1 Available)
**Owner**: lead-os (Project Owner), tiger-coder (Executor)
**Timeline**: Week 1-2 (2026-04-02 ~ 2026-04-13)
**Status**: In Progress

---

## 一、目标

V1 可用底座：

1. 定义 run event schema v1
2. SQLite 存储：event_log + run_state
3. gateway-lite-v1 作为第一批 producer
4. 支持 run timeline 查询/查看

---

## 二、核心 Schema

### event_log (append-only)

```json
{
  "event_id": "uuid",
  "run_id": "唯一标识",
  "thread_id": "线程标识",
  "project_id": "项目标识",
  "task_id": "任务标识",
  "agent_id": "执行agent",
  "capability_id": "调用能力",
  "event_type": "created/running/completed/failed/blocked/skipped/approved/escalated",
  "status": "success/failure/pending",
  "cost": 0.00,
  "latency_ms": 0,
  "artifacts": [],
  "approvals": [],
  "interrupts": [],
  "resume_points": [],
  "escalation": {},
  "errors": [],
  "metadata": {},
  "timestamp": "ISO8601"
}
```

### run_state (当前状态快照)

```json
{
  "run_id": "唯一标识",
  "project_id": "项目标识",
  "task_id": "任务标识",
  "current_agent_id": "当前执行agent",
  "current_stage": "planning/drafting/reviewing/exporting",
  "status": "created/running/completed/failed/blocked/skipped",
  "started_at": "ISO8601",
  "updated_at": "ISO8601",
  "checkpoint_ref": "可选恢复点"
}
```

---

## 三、存储结构

| Table | 用途 | 特点 |
|-------|------|------|
| event_log | 事件流水 | append-only，按 run_id + timestamp 索引 |
| run_state | 当前状态 | 快照，实时更新，按 run_id 唯一 |

---

## 四、Producer 接入

### 第一批：gateway-lite-v1

每次 gateway 调用自动写入：

- 调用开始 → event_type: "created"
- 调用完成 → event_type: "completed" / "failed"
- 超时/降级 → event_type: "skipped" / "escalated"

### 后续接入

- routing-layer-v1
- checkpoint-resume-v1
- 各 agent 执行链路

---

## 五、Consumer 接入

### 第一批：control-center-v1

- 按 run_id 查询事件时间线
- run 状态展示
- 基础 timeline 视图

### 后续接入

- memory layer
- evidence layer
- diagnostics

---

## 六、Week 1 交付清单

| # | 交付项 | 说明 |
|---|--------|------|
| 1 | Schema 定义 | event_log + run_state 的 JSON Schema |
| 2 | SQLite 表结构 | CREATE TABLE 语句 |
| 3 | 写入模块 | gateway-lite-v1 集成，写入 event_log |
| 4 | 查询接口 | 按 run_id 获取 timeline |
| 5 | 基础视图 | control-center 接入，展示 timeline |

---

## 七、验收标准

- ✅ 一个 run 有统一 run_id
- ✅ 关键事件能写入 ledger
- ✅ 能按 run 查询事件时间线
- ✅ control-center-v1 可接入此时间线

---

## 八、后续演进

- P1: 扩展字段 (更多 metadata)
- P2: 接入更多 producer
- P3: 性能优化 / Postgres 迁移

---

## Registry

| Field | Value |
|-------|-------|
| project | run-ledger-v1 |
| version | 1.0 |
| owner | lead-os |
| executor | tiger-coder |
| started | 2026-04-02 |

---

*This is the working document for Run Ledger v1.*