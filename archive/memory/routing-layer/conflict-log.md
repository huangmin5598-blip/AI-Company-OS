# 冲突日志 — Routing Layer V1

**版本**: 1.0
**更新时间**: 2026-03-31

---

## 试验记录

### 试验 1: 共享 Agent 冲突 (2026-03-31 12:22)

**类型**: 共享 Agent 冲突
**冲突 Agent**: tiger-coder
**触发任务**:
- 任务 A: gateway-lite-v1 维护 (09:00 Heartbeat)
- 任务 B: control-center-v1 模块开发 (用户触发)

**检测结果**:
- route_type: exception
- route_reason: shared_agent_conflict
- agent: tiger-coder
- tasks: [task-A, task-B]

**处理策略**: queue

**决策**:
- 先执行任务 A (gateway-lite 维护)
- 任务 B 进入队列等待

**结果**: ✅ 通过 - 系统识别冲突，按 queue 策略处理

---

## 冲突统计

| 日期 | 类型 | Agent | 策略 | 结果 |
|------|------|-------|------|------|
| 2026-03-31 | shared_agent | tiger-coder | queue | ✅ 通过 |

---

### 试验 2: 优先级冲突 (2026-03-31 12:23)

**类型**: 优先级冲突
**触发任务**:
- 任务 A: Daily Report 生成 (system, priority: high)
- 任务 B: novel-v1 writer (project, priority: normal)

**检测结果**:
- route_type: exception
- route_reason: priority_conflict
- high_priority_task: Daily Report
- normal_priority_task: novel-v1 writer

**处理策略**: delay

**决策**:
- 先执行任务 A (Daily Report, high priority)
- 任务 B (writer) 延迟执行，等待 A 完成

**结果**: ✅ 通过 - 系统识别优先级冲突，按 delay 策略处理

**说明**: system task 优先于 project task 是合理的设计，确保系统报告不延迟

---

## next_step

- 等待更多冲突场景触发
- 补充优先级冲突试验
