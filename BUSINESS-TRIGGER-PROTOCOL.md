# Business Trigger Execution Protocol

**Version**: 1.0
**Created**: 2026-04-01
**Purpose**: Execution layer closure for business guarantee triggers

---

## 一、Business Trigger 响应流程

当 main session 收到以下 trigger 时，必须执行：

| Trigger | 必须执行的动作 |
|---------|----------------|
| `novel-daily` | 检查今日 novel-v1 最低保障，若未满足，创建任务 |
| `research-weekly` | 检查本周 research-agent 最低保障，若未满足，创建任务 |
| `product-weekly` | 检查本周产品项目最低保障，若未满足，创建任务 |

---

## 二、执行逻辑 (必须执行)

### Step 1: 检查最低保障状态

```
IF trigger == "novel-daily":
    CHECK: 今日是否已有 novel-v1 任务
    IF 已存在:
        LOG: "今日 novel-v1 最低保障已满足，跳过"
        UPDATE audit_fields: skipped, skip_reason="already_satisfied"
    ELSE:
        GOTO Step 2
```

### Step 2: 创建业务任务

```
IF trigger == "novel-daily":
    CREATE task: novel-XXX-task-card.md
    SET task_status = "created"
    UPDATE audit_fields: task_created=true, task_id=XXX

IF trigger == "research-weekly":
    CREATE research task
    SET task_status = "created"
    UPDATE audit_fields: task_created=true

IF trigger == "product-weekly":
    CREATE product task
    SET task_status = "created"
    UPDATE audit_fields: task_created=true
```

### Step 3: 写入 Audit Fields

```
audit_record = {
    "trigger": "novel-daily",
    "timestamp": "2026-04-02T08:00:00",
    "task_created": true,
    "task_id": "novel-27",
    "execution_mode": "standard/lite/resume",
    "result": "success/skipped/blocked/failed",
    "skip_reason": null,
    "blocked_reason": null,
    "rescue_used": false
}
```

---

## 三、最小降级执行逻辑

### 执行模式定义

| Mode | 描述 | 适用场景 |
|------|------|----------|
| **standard** | 完整执行链路 (lead-novel → story-editor → writer → review-editor) | 资源充足，正常执行 |
| **lite** | 简化执行 (只跑 writer + review，跳过 story-editor) | 资源不足，但保证产出 |
| **resume** | 从 checkpoint 恢复执行 | 之前有失败，从断点继续 |
| **blocked** | 任务阻塞，无法执行 | 资源完全不足，需记录原因 |
| **skipped** | 显式跳过 | 已满足最低保障或特殊原因 |

### 自动选择逻辑

```
IF resources_充足:
    execution_mode = "standard"
ELIF resources_不足但可产出:
    execution_mode = "lite"
ELIF 有 checkpoint:
    execution_mode = "resume"
ELIF resources_完全不足:
    execution_mode = "blocked"
    必须记录 blocked_reason
```

---

## 四、跳过与自动批准规则

### 可自动创建 (无需 CEO 审批)

| 场景 | 动作 |
|------|------|
| 今日无 novel-v1 任务 | 自动创建 |
| 本周无 research 任务 | 自动创建 |
| 本周无产品推进任务 | 自动创建 |

### 必须升级给 CEO

| 场景 | 动作 |
|------|------|
| 连续 3 天 novel-v1 被 blocked | 升级 CEO 决策 |
| 连续 2 周 research 无产出 | 升级 CEO 决策 |
| 任何项目需要跳过 (skipped) | 记录 skip_reason，但下次需 CEO 确认 |

### 允许 Skipped 的情况 (必须写原因)

| 场景 | skip_reason |
|------|-------------|
| 今日已有任务 | already_satisfied |
| 周末/节假日 | weekend_holiday |
| CEO 显式批准跳过 | approved_by_ceo |
| 系统维护中 | system_maintenance |

---

## 五、Audit Fields 写入要求

所有 business trigger 执行后，必须写入：

```json
{
  "trigger": "novel-daily",
  "trigger_time": "2026-04-02T08:00:00+08:00",
  "project_id": "novel-v1",
  "expected_to_run": true,
  "task_created": true,
  "task_id": "novel-27",
  "task_dispatched": true,
  "execution_mode": "standard",
  "result": "success",
  "skip_reason": null,
  "blocked_reason": null,
  "rescue_used": false,
  "logged_at": "2026-04-02T08:01:00+08:00"
}
```

---

## 六、禁止事项

- ❌ 收到 trigger 但不执行任何动作
- ❌ 不写 audit_fields 就跳过
- ❌ skip_reason 为空
- ❌ blocked_reason 为空但状态是 blocked

---

## 七、明天验证清单

1. ✅ cron job 确实触发
2. ✅ main session 确实响应
3. ✅ 确实创建了业务任务
4. ✅ 确实写入了 audit fields (本 protocol 保证)

---

## Registry

| Field | Value |
|-------|-------|
| document_type | business-trigger-execution-protocol |
| version | 1.0 |
| created | 2026-04-01 |
| owner | main (CEO) |
| status | P0 - Ready for validation |

---

*This protocol ensures business triggers are actually executed with audit.*