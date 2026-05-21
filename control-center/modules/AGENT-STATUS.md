# Agent Status — Control Center V1 模块

**版本**: 1.0
**更新时间**: 2026-03-31
**模块**: Control Center V1 - Module 2

---

## 一、模块说明

Agent Status 是 control-center-v1 P0 的第二个模块，负责展示所有 Agent 的状态概览。

**数据源**：
- `openclaw agents list` → Agent 列表、模型、配置
- `execution-records.json` → Agent 执行记录、timeout/fallback
- `CAPABILITY-REGISTRY.md` → Agent 能力定义

---

## 二、字段定义

| 字段 | 描述 | 必填 | 数据来源 |
|------|------|------|----------|
| agent_id | Agent 唯一标识 | ✅ | openclaw |
| role | 角色定义 | ✅ | CAPABILITY-REGISTRY |
| current_status | 当前状态 | ✅ | execution-records (idle/working/blocked/error) |
| last_active_at | 最近活跃时间 | - | execution-records |
| timeout_count | 超时次数 | - | execution-records |
| fallback_count | fallback 次数 | - | execution-records |
| related_project | 关联项目 | - | CAPABILITY-REGISTRY |
| last_task_id | 最近任务 ID | - | execution-records |
| model | 使用模型 | ✅ | openclaw |

---

## 三、状态定义

### 当前状态 (current_status)

| 状态 | 描述 |
|------|------|
| idle | 空闲 |
| working |工作中 |
| blocked | 阻塞 |
| error | 错误 |

### 状态判定逻辑

```python
def get_agent_status(agent_id, execution_records):
    # 1. 检查 execution-records 中该 agent 最近活动
    recent_task = get_recent_task(agent_id, execution_records)
    
    if recent_task is None:
        return "idle"
    
    if recent_task.status == "running":
        return "working"
    
    if recent_task.autonomy_status == "main_rescue":
        return "blocked"
    
    if recent_task.status == "error":
        return "error"
    
    return "idle"
```

---

## 四、Daily 简版

### 输出格式

```markdown
## Agent Status

| Agent | Role | Status | Last Active |
|-------|------|--------|-------------|
| main | CEO 助手 | idle | 2026-03-31 12:00 |
| lead-novel | 项目 Lead | idle | 2026-03-31 08:00 |
| story-editor | 结构设计 | idle | 2026-03-31 08:00 |
| writer | 内容生产 | idle | 2026-03-31 08:11 |
| review-editor | 质量控制 | idle | 2026-03-31 08:00 |
| research-agent | 机会研究 | idle | 2026-03-31 06:00 |
| tiger-coder | 系统开发 | working | 2026-03-31 12:22 |
```

### 统计行

```
总计: 14 Agents
工作中: 1
空闲: 12
阻塞: 1 (novel-v1 writer 曾 timeout)
错误: 0
```

---

## 五、Weekly 完整版

### 输出格式

```markdown
# Agent Status — Week 15, 2026-03-31

## Agent 总览

| # | Agent | Role | Status | Last Active | Timeout | Fallback | Project |
|---|-------|------|--------|-------------|---------|----------|---------|
| 1 | main | CEO 助手 | idle | 2026-03-31 12:00 | 0 | 0 | - |
| 2 | lead-novel | 项目 Lead | idle | 2026-03-31 08:00 | 0 | 0 | novel-v1 |
| 3 | story-editor | 结构设计 | idle | 2026-03-31 08:00 | 0 | 0 | novel-v1 |
| 4 | writer | 内容生产 | idle | 2026-03-31 08:11 | 1 | 0 | novel-v1 |
| 5 | review-editor | 质量控制 | idle | 2026-03-31 08:00 | 0 | 0 | novel-v1 |
| 6 | research-agent | 机会研究 | idle | 2026-03-31 06:00 | 0 | 0 | research-agent |
| 7 | tiger-coder | 系统开发 | working | 2026-03-31 12:22 | 0 | 0 | gateway-lite |
| 8 | lead-hub | 项目 Lead | idle | 2026-03-16 | 0 | 0 | hub-v1 |
| 9 | lead-sticker | 项目 Lead | idle | 2026-03-16 | 0 | 0 | sticker-v1 |
| 10 | lead-motionclean | 项目 Lead | idle | 2026-03-20 | 0 | 0 | motionclean-v1 |
| 11 | finance-analyst | 金融分析 | idle | - | 0 | 0 | finance-ops |
| 12 | content-manager | 内容管理 | idle | - | 0 | 0 | hub-v1 |
| 13 | amazon-seller | 亚马逊卖家 | idle | - | 0 | 0 | amazon |
| 14 | course-builder | 课程构建 | idle | - | 0 | 0 | course |

## 统计

- **总计**: 14 Agents
- **工作中**: 1
- **空闲**: 12
- **阻塞**: 1 (writer timeout 已恢复)
- **错误**: 0

## 超时/失败详情

### writer (novel-v1)
- **Timeout**: 1 次 (novel-26, 30s)
- **Fallback**: 0 次
- **恢复方式**: resumed from checkpoint
- **最近任务**: novel-26 (密室解剖师)
```

---

## 六、读取逻辑

```python
# 伪代码

def read_agent_status():
    # 1. 读取 openclaw agents list
    all_agents = openclaw_agents_list()
    
    # 2. 读取 execution-records
    records = read_execution_records()
    
    # 3. 读取 capability-registry
    capabilities = read_capability_registry()
    
    # 4. 合并数据
    status_list = []
    for agent in all_agents:
        record = records.get(agent.id)
        capability = capabilities.get(agent.id)
        
        status_list.append({
            "agent_id": agent.id,
            "role": capability.role if capability else "unknown",
            "current_status": get_agent_status(agent.id, records),
            "last_active_at": record.last_active if record else None,
            "timeout_count": record.timeout_count if record else 0,
            "fallback_count": record.fallback_count if record else 0,
            "related_project": capability.supported_projects if capability else None,
            "last_task_id": record.last_task_id if record else None,
            "model": agent.model
        })
    
    return status_list
```

---

## 七、验收标准

| 标准 | 状态 |
|------|------|
| Founder 能一眼看清当前 Agent 列表与状态 | ✅ |
| 能区分 idle/working/blocked/error | ✅ |
| 能看到最近活跃时间 | ✅ |
| 能看到 timeout/fallback 基本情况 | ✅ |
| 可作为后续 Gateway/Routing/CEO 模块基础 | ✅ |

---

## 八、与 Project Board 的关系

- Agent Status 依赖 Project Board 定义的项目
- 每个 Agent 必须关联到具体 Project
- Project Board 展示项目，Agent Status 展示执行者

---

## 九、next_step

整合到 Daily Report 18:00 输出中，作为 Project Board 后的第二个模块。
