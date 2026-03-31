# Gateway Summary — Control Center V1 模块

**版本**: 1.0
**更新时间**: 2026-03-31
**模块**: Control Center V1 - Module 3

---

## 一、模块说明

Gateway Summary 是 control-center-v1 P0 的第三个模块，负责展示模型调用的成本与治理数据。

**数据源**：
- `gateway-lite/daily/YYYY-MM-DD.json` → 每日成本记录
- `gateway-lite/weekly/week-N.md` → 每周汇总
- `gateway-lite/OPERATIONS.md` → 运营配置

---

## 二、字段定义

| 字段 | 描述 | 必填 | 数据来源 |
|------|------|------|----------|
| report_period | 报告周期 | ✅ | gateway-lite |
| total_calls | 总调用次数 | ✅ | gateway-lite |
| total_cost_usd | 总成本（美元）| ✅ | gateway-lite |
| fallback_count | fallback 次数 | ✅ | gateway-lite |
| warning_count | warning 次数 | - | gateway-lite |
| last_warning | 最近 warning | - | gateway-lite |
| top_agents_by_cost | Agent 成本 TOP | - | gateway-lite |
| top_projects_by_cost | 项目成本 TOP | - | gateway-lite |

---

## 三、Daily 简版

### 输出格式

```markdown
## Gateway Summary

| Period | Total Calls | Total Cost | Fallback | Warning |
|--------|-------------|------------|----------|---------|
| 2026-03-31 | 8 | $0.00255 | 2 | 0 |

### Top Agents by Cost
1. research-agent: $0.00050
2. story-editor: $0.00043
3. writer: $0.00043

### Fallback Summary
- **总计**: 2 次
- **原因**: timeout (2)
```

---

## 四、Weekly 完整版

### 输出格式

```markdown
# Gateway Summary — Week 15, 2026-03-31

## 周度概览

| Period | Total Calls | Total Cost | Fallback | Warning |
|--------|-------------|------------|----------|---------|
| Week 15 | 56 | $0.01785 | 14 | 0 |

### Agent 成本 TOP 3

| # | Agent | Cost (USD) | % of Total |
|---|-------|------------|------------|
| 1 | writer | $0.00600 | 33.6% |
| 2 | research-agent | $0.00450 | 25.2% |
| 3 | lead-novel | $0.00300 | 16.8% |

### 项目成本 TOP 3

| # | Project | Cost (USD) | % of Total |
|---|---------|------------|------------|
| 1 | novel-v1 | $0.01000 | 56% |
| 2 | research-agent | $0.00500 | 28% |
| 3 | hub-v1 | $0.00285 | 16% |

### Fallback 趋势

| 日期 | Fallback Count | 原因分布 |
|------|----------------|----------|
| 2026-03-30 | 2 | timeout: 2 |
| 2026-03-29 | 1 | rate_limit: 1 |
| 2026-03-28 | 3 | timeout: 2, error: 1 |

### Warning 摘要

- **当前 Warning**: 0
- **最近 Warning**: 无

### 成本趋势

```
Week 12: $0.01200
Week 13: $0.01500 (+25%)
Week 14: $0.01650 (+10%)
Week 15: $0.01785 (+8%)
```

---

## 五、数据读取逻辑

### 读取每日数据

```python
# 伪代码

def read_daily_gateway_summary(date):
    daily_file = f"gateway-lite/daily/{date}.json"
    data = read_json(daily_file)
    
    # 按 agent 聚合成本
    agent_costs = {}
    for entry in data.entries:
        agent_costs[entry.agent_id] = agent_costs.get(entry.agent_id, 0) + entry.estimated_cost_usd
    
    # 排序 TOP 3
    top_agents = sorted(agent_costs.items(), key=lambda x: x[1], reverse=True)[:3]
    
    return {
        "report_period": date,
        "total_calls": data.summary.total_calls,
        "total_cost_usd": data.summary.total_cost_usd,
        "fallback_count": data.summary.fallback_count,
        "warning_count": 0,  # 从运营配置获取
        "last_warning": None,
        "top_agents_by_cost": top_agents
    }
```

### 读取每周数据

```python
def read_weekly_gateway_summary(week_id):
    weekly_file = f"gateway-lite/weekly/week-{week_id}.md"
    data = read_markdown(weekly_file)
    
    return {
        "report_period": f"Week {week_id}",
        "total_calls": data.total_calls,
        "total_cost_usd": data.total_cost_usd,
        "fallback_count": data.fallback_count,
        "warning_count": data.warning_count,
        "agent_ranking": data.agent_ranking,
        "project_ranking": data.project_ranking,
        "fallback_trend": data.fallback_trend
    }
```

---

## 六、数据源字段映射

| gateway-lite 字段 | control-center 字段 |
|-------------------|---------------------|
| summary.total_calls | total_calls |
| summary.total_cost_usd | total_cost_usd |
| summary.fallback_count | fallback_count |
| entries[].agent_id | top_agents_by_cost |
| entries[].estimated_cost_usd | (聚合后使用) |
| entries[].fallback_triggered | fallback_count 统计 |

---

## 七、验收标准

| 标准 | 状态 |
|------|------|
| Founder 能一眼看清当前成本与 fallback 情况 | ✅ |
| 能区分 Agent 成本与项目成本 | ✅ |
| 能看到 warning 状态 | ✅ |
| 数据来源清晰，复用 gateway-lite 数据 | ✅ |
| 可作为后续模块基础 | ✅ |

---

## 八、与 Project Board / Agent Status 的关系

- Gateway Summary 补充了执行层的成本视角
- Project Board 展示项目状态，Gateway Summary 展示项目成本
- Agent Status 展示 Agent 运行状态，Gateway Summary 展示 Agent 成本

---

## 九、next_step

整合到 Daily Report 18:00 输出中，作为 Agent Status 后的第三个模块。
