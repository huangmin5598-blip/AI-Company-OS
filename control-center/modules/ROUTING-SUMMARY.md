# Routing Summary — Control Center V1 模块

**版本**: 1.0
**更新时间**: 2026-03-31
**模块**: Control Center V1 - Module 5

---

## 一、模块说明

Routing Summary 是 control-center-v1 P0 的第五个模块，负责展示系统路由与流转情况。

**数据源**：
- `ROUTING-RULES.md` → 路由规则定义
- `memory/routing-layer/conflict-log.md` → 冲突处理日志
- `execution-records.json` → routing/resume/main_rescue 记录
- `checkpoint-resume-v1` → resume 状态

---

## 二、字段定义

| 字段 | 描述 | 必填 | 数据来源 |
|------|------|------|----------|
| route_type | 路由类型 | ✅ | ROUTING-RULES |
| route_reason | 路由原因 | ✅ | ROUTING-RULES |
| next_agent | 下一个 Agent | ✅ | ROUTING-RULES |
| fallback_agent | Fallback Agent | - | ROUTING-RULES |
| escalation_to | 升级目标 | - | ROUTING-RULES |
| timeout_stage | 超时阶段 | - | execution-records |
| autonomy_status | 自主状态 | - | execution-records |
| conflict_type | 冲突类型 | - | conflict-log |
| conflict_result | 冲突处理结果 | - | conflict-log |

---

## 三、Daily 简版

### 输出格式

```markdown
## Routing Summary

### 今日 Route 命中
| Type | Reason | Target | Count |
|------|--------|--------|-------|
| message | project | novel-v1 | 1 |
| task | novel-daily | writer | 2 |
| exception | timeout | resume | 1 |

### Resume / Main Rescue
- **Resume**: 1 (writer, novel-26, from checkpoint)
- **Main Rescue**: 1 (novel-v1, subagent timeout)

### 冲突处理
- **共享 Agent 冲突**: 1 (tiger-coder) → queue
- **优先级冲突**: 1 (system vs project) → delay
```

---

## 四、Weekly 完整版

### 输出格式

```markdown
# Routing Summary — Week 15, 2026-03-31

## Route 命中分布

| Route Type | Count | % |
|------------|-------|---|
| message → project | 5 | 35% |
| message → on-demand | 3 | 21% |
| message → system | 2 | 14% |
| task → novel-daily | 14 | 100% |
| task → research-weekly | 3 | 21% |
| exception → resume | 4 | 29% |
| exception → fallback | 2 | 14% |
| exception → main_rescue | 1 | 7% |

## Timeout / Resume / Main Rescue 汇总

| Stage | Count | Recovery |
|-------|-------|----------|
| writer timeout | 4 | 3 resume, 1 main_rescue |
| story-editor timeout | 2 | 2 resume |
| lead-novel timeout | 0 | - |

### Resume 详情

| Task ID | Agent | Checkpoint | Result |
|---------|-------|------------|--------|
| novel-26 | writer | structure | resumed |
| novel-25 | writer | draft-progress | resumed |
| novel-23 | story-editor | task-init | resumed |

### Main Rescue 详情

| Task ID | Reason | Result |
|---------|--------|--------|
| novel-23 | subagent timeout, no checkpoint | main_rescue |

## 冲突处理记录

| 日期 | 冲突类型 | Agent/优先级 | 策略 | 结果 |
|------|----------|--------------|------|------|
| 2026-03-31 | 共享 Agent | tiger-coder | queue | ✅ |
| 2026-03-31 | 优先级 | system vs project | delay | ✅ |

## CEO / Project Lead 升级情况

| 升级类型 | Count | 原因 |
|----------|-------|------|
| 规则未命中 | 0 | - |
| 多项目冲突 | 1 | tiger-coder 共享 |
| 严重异常 | 0 | - |
| main_rescue 失败 | 0 | - |

### 升级详情

- **多项目冲突**: 2026-03-31, tiger-coder 被 novel-v1 和 hub-v1 同时请求 → queue 策略处理 → 无需升级
```

---

## 五、数据读取逻辑

```python
# 伪代码

def read_routing_summary():
    # 1. 读取 ROUTING-RULES
    rules = read_routing_rules()
    
    # 2. 读取冲突日志
    conflict_log = read_conflict_log()
    
    # 3. 读取 execution-records
    records = read_execution_records()
    
    # 4. 读取 checkpoint-resume 状态
    checkpoint_status = read_checkpoint_resume_status()
    
    # 5. 统计 route 命中
    route_stats = {
        "message_project": 0,
        "message_on_demand": 0,
        "message_system": 0,
        "task_novel": 0,
        "task_research": 0,
        "exception_resume": 0,
        "exception_fallback": 0,
        "exception_main_rescue": 0
    }
    
    # 6. 统计 resume/main_rescue
    resume_count = 0
    main_rescue_count = 0
    for task in records.tasks:
        if task.autonomy_status == "resumed":
            resume_count += 1
        elif task.autonomy_status == "main_rescue":
            main_rescue_count += 1
    
    # 7. 统计冲突处理
    conflict_stats = {
        "shared_agent": 0,
        "priority": 0,
        "escalate": 0
    }
    for conflict in conflict_log:
        if conflict.type == "shared_agent":
            conflict_stats["shared_agent"] += 1
        elif conflict.type == "priority":
            conflict_stats["priority"] += 1
    
    return {
        "route_stats": route_stats,
        "resume_count": resume_count,
        "main_rescue_count": main_rescue_count,
        "conflict_stats": conflict_stats,
        "escalation_count": 0  # 通过规则计算
    }
```

---

## 六、路由类型说明

| Route Type | Description |
|------------|-------------|
| message → project | Founder 输入进入项目池 |
| message → on-demand | Founder 输入直接响应 |
| message → system | Founder 输入进入系统命令 |
| task → novel-daily | 小说日常任务 |
| task → research-weekly | 研究每周任务 |
| exception → resume | 超时有 checkpoint，恢复 |
| exception → fallback | 超时无 checkpoint，fallback 重试 |
| exception → main_rescue | fallback 也失败，main 介入 |

---

## 七、验收标准

| 标准 | 状态 |
|------|------|
| Founder 一眼看清主要路由命中 | ✅ |
| 能看到 timeout/resume/main_rescue 流转 | ✅ |
| 能看到冲突处理摘要 | ✅ |
| 数据来源清晰，复用 routing-layer | ✅ |
| 可作为 CEO Escalation / System Health 基础 | ✅ |

---

## 八、与前面模块的关系

- **Project Board**: 项目视角
- **Agent Status**: Agent 视角
- **Gateway Summary**: 成本视角
- **Capability Overview**: 能力视角
- **Routing Summary**: 流转视角

五者结合：项目 → Agent → 能力 → 成本 → 流转 = 完整系统视图

---

## 九、next_step

整合到 Daily Report 18:00 输出中，作为 Capability Overview 后的第五个模块。
