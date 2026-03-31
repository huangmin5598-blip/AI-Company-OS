# CEO Escalation Summary — Control Center V1 模块

**版本**: 1.0
**更新时间**: 2026-03-31
**模块**: Control Center V1 - Module 6

---

## 一、模块说明

CEO Escalation Summary 是 control-center-v1 P0 的第六个模块，负责展示 CEO/ main 介入事项。

**数据源**：
- `ROUTING-RULES.md` → CEO 介入条件
- `execution-records.json` → escalation/rescue 记录
- `memory/routing-layer/conflict-log.md` → 冲突升级
- `TASK-POOL.md` → blocked 项目

---

## 二、字段定义

| 字段 | 描述 | 必填 | 数据来源 |
|------|------|------|----------|
| escalation_id | 升级唯一标识 | ✅ | 系统生成 |
| source_event | 触发事件 | ✅ | execution-records |
| escalation_to | 升级目标 | ✅ | ROUTING-RULES |
| escalation_reason | 升级原因 | ✅ | ROUTING-RULES |
| related_project | 相关项目 | - | execution-records |
| related_task | 相关任务 | - | execution-records |
| current_status | 当前状态 | ✅ | 系统状态 (pending/handled/resolved) |
| founder_attention_needed | 是否需要 Founder 关注 | - | 判定 |

---

## 三、升级类型说明

| 类型 | 描述 | 来源 |
|------|------|------|
| routing | 规则未命中、多项目冲突 | ROUTING-RULES |
| blocked | 项目阻塞、项目 Lead 无法解决 | TASK-POOL |
| main_rescue | subagent 失败，main 介入 | execution-records |
| conflict | 共享 Agent 冲突无法自动解决 | conflict-log |
| system | 系统级问题（data loss, error） | 系统 |

---

## 四、Daily 简版

### 输出格式

```markdown
## CEO Escalation Summary

### 今日升级事项
| # | Source | Reason | Project | Status | Attention |
|---|--------|--------|---------|--------|-----------|
| 1 | main_rescue | subagent timeout | novel-v1 | resolved | No |
| 2 | conflict | shared agent (tiger-coder) | - | handled | No |

### 未关闭事项
- **无**

### Founder 需关注
- **无**
```

---

## 五、Weekly 完整版

### 输出格式

```markdown
# CEO Escalation Summary — Week 15, 2026-03-31

## 升级类型分布

| Type | Count | % |
|------|-------|---|
| main_rescue | 3 | 50% |
| conflict | 2 | 33% |
| blocked | 1 | 17% |
| routing | 0 | 0% |
| system | 0 | 0% |

## 升级原因分析

| 原因 | Count | 占比 |
|------|-------|------|
| subagent timeout | 3 | 50% |
| shared agent conflict | 2 | 33% |
| project blocked | 1 | 17% |

### 高发原因

1. **subagent timeout** (50%)
   - 主要发生在 writer 阶段
   - checkpoint-resume-v1 P0 已通过，可减少此类升级

2. **shared agent conflict** (33%)
   - tiger-coder 被多项目同时请求
   - routing-layer-v1 queue 策略已处理

3. **project blocked** (17%)
   - motionclean-v1 因资源问题暂停
   - 已解决

## 升级详情

| ID | Source | Reason | Project | Task | Status | Date |
|----|--------|--------|---------|------|--------|------|
| ESC-001 | main_rescue | writer timeout, no checkpoint | novel-v1 | novel-23 | resolved | 2026-03-31 |
| ESC-002 | main_rescue | writer timeout, checkpoint available | novel-v1 | novel-26 | resolved | 2026-03-31 |
| ESC-003 | conflict | shared agent (tiger-coder) | - | - | handled | 2026-03-31 |
| ESC-004 | conflict | priority conflict (system vs project) | - | - | handled | 2026-03-31 |
| ESC-005 | main_rescue | story-editor timeout | novel-v1 | novel-25 | resolved | 2026-03-30 |
| ESC-006 | blocked | resource dependent | motionclean-v1 | - | resolved | 2026-03-28 |

## 当前未关闭事项

| ID | Source | Reason | Status |
|----|--------|--------|--------|
| - | - | 无未关闭事项 | - |

## Founder 需关注

**当前无需关注事项**

所有升级事项均已 resolved/handled。

---

## 六、数据读取逻辑

```python
# 伪代码

def read_ceo_escalation_summary():
    # 1. 读取 execution-records 中的 rescue 相关记录
    records = read_execution_records()
    
    # 2. 读取冲突日志
    conflict_log = read_conflict_log()
    
    # 3. 读取 TASK-POOL 中 blocked 项目
    blocked_projects = read_task_pool_blocked()
    
    # 4. 构建升级列表
    escalations = []
    
    # main_rescue
    for task in records.tasks:
        if task.autonomy_status == "main_rescue":
            escalations.append({
                "escalation_id": f"ESC-{len(escalations)+1:03d}",
                "source_event": "main_rescue",
                "escalation_to": "main",
                "escalation_reason": f"{task.agent} timeout, {task.reason}",
                "related_project": task.project,
                "related_task": task.id,
                "current_status": "resolved",
                "founder_attention_needed": False
            })
    
    # conflict
    for conflict in conflict_log.conflicts:
        escalations.append({
            "escalation_id": f"ESC-{len(escalations)+1:03d}",
            "source_event": "conflict",
            "escalation_to": "main",
            "escalation_reason": f"{conflict.type} ({conflict.agent})",
            "related_project": None,
            "related_task": None,
            "current_status": "handled",
            "founder_attention_needed": False
        })
    
    # blocked
    for project in blocked_projects:
        if project.block_reason and project.block_escalation:
            escalations.append({
                "escalation_id": f"ESC-{len(escalations)+1:03d}",
                "source_event": "blocked",
                "escalation_to": "project_lead",
                "escalation_reason": project.block_reason,
                "related_project": project.id,
                "related_task": None,
                "current_status": "resolved" if project.unblocked else "pending",
                "founder_attention_needed": project.unblocked == False
            })
    
    # 5. 统计
    type_counts = {}
    for esc in escalations:
        type_counts[esc.source_event] = type_counts.get(esc.source_event, 0) + 1
    
    pending_count = sum(1 for esc in escalations if esc.current_status == "pending")
    attention_needed = sum(1 for esc in escalations if esc.founder_attention_needed)
    
    return {
        "total_escalations": len(escalations),
        "type_counts": type_counts,
        "pending_count": pending_count,
        "attention_needed": attention_needed,
        "escalations": escalations
    }
```

---

## 七、验收标准

| 标准 | 状态 |
|------|------|
| Founder 一眼看清升级到 CEO 的事项 | ✅ |
| 能看到升级原因与来源 | ✅ |
| 能区分 pending/handled/resolved | ✅ |
| 数据来源清晰，复用 routing/conflict/rescue | ✅ |
| 可作为 System Health 前置基础 | ✅ |

---

## 八、与前面模块的关系

| 模块 | 视角 | CEO Escalation 关联 |
|------|------|---------------------|
| Project Board | 项目 | blocked 项目 |
| Agent Status | Agent | timeout 统计 |
| Gateway Summary | 成本 | fallback 关联 |
| Capability Overview | 能力 | 能力缺口关联 |
| Routing Summary | 流转 | 升级来源 |

CEO Escalation Summary 是所有模块的"汇总输出"视角。

---

## 九、next_step

整合到 Daily Report 18:00 输出中，作为 Routing Summary 后的第六个模块。
