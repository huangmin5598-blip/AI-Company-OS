# Capability Overview — Control Center V1 模块

**版本**: 1.0
**更新时间**: 2026-03-31
**模块**: Control Center V1 - Module 4

---

## 一、模块说明

Capability Overview 是 control-center-v1 P0 的第四个模块，负责展示系统能力地图。

**数据源**：
- `CAPABILITY-REGISTRY.md` → Agent 能力定义
- `Skills Gap Review` → 能力缺口分析

---

## 二、字段定义

| 字段 | 描述 | 必填 | 数据来源 |
|------|------|------|----------|
| agent_id | Agent 唯一标识 | ✅ | CAPABILITY-REGISTRY |
| role | 角色定义 | ✅ | CAPABILITY-REGISTRY |
| core_capabilities | 核心能力 | ✅ | CAPABILITY-REGISTRY |
| boundaries | 能力边界 | ✅ | CAPABILITY-REGISTRY |
| supported_projects | 支持的项目 | ✅ | CAPABILITY-REGISTRY |
| key_gap | 关键缺口 | - | Skills Gap Review |
| related_workflows | 关联工作流 | - | CAPABILITY-REGISTRY |
| related_protocols | 关联协议 | - | CAPABILITY-REGISTRY |

---

## 三、Daily 简版

### 输出格式

```markdown
## Capability Overview

### 核心 Agent 概览
- **总计**: 9 Core Agents
- **System Agents**: 1

### 能力覆盖情况
| Category | Status | Notes |
|----------|--------|-------|
| 内容生产 | ✅ 完整 | lead-novel → story-editor → writer → review-editor |
| 机会研究 | ✅ 完整 | research-agent |
| 系统开发 | ✅ 完整 | tiger-coder |
| 金融分析 | ✅ 完整 | finance-analyst |
| 项目管理 | ✅ 完整 | lead-* (4个项目) |

### 关键缺口提醒
- **多 Agent 调度**: 已具备（Heartbeat）
- **复杂路由**: routing-layer-v1 P0 进行中
- **实时监控**: preflight-diagnostics-v1 待启动
```

---

## 四、Weekly 完整版

### 输出格式

```markdown
# Capability Overview — Week 15, 2026-03-31

## Agent 能力总览

| # | Agent | Role | Core Capabilities | Boundaries | Projects |
|---|-------|------|-------------------|------------|----------|
| 1 | main | CEO助手 | 任务分发, 决策支持, 项目管理, 调度 | 不参与具体写作/开发 | 全项目 |
| 2 | lead-novel | 项目Lead | 选题生成, Task Card 创建, 任务调度, 验收 | 不负责正文写作/审核 | novel-v1 |
| 3 | story-editor | 结构设计 | 大纲生成, 章节规划, 结构审核 | 不负责正文写作 | novel-v1 |
| 4 | writer | 内容生产 | 正文写作, 场景描写, 对话创作 | 不负责审核/校对 | novel-v1 |
| 5 | review-editor | 质量控制 | 内容审核, 质量评估, PASS/REVISION | 不负责写作 | novel-v1 |
| 6 | research-agent | 机会研究 | 市场扫描, 竞品分析, 机会识别 | 不负责项目执行 | research-agent |
| 7 | finance-analyst | 金融分析 | 财务报表分析, 投资建议 | 不负责投资决策 | finance-ops |
| 8 | tiger-coder | 系统开发 | 代码编写, 方案设计, 系统架构 | 不负责业务逻辑 | gateway-lite, control-center, routing-layer |
| 9 | content-manager | 内容管理 | 内容规划, 发布管理 | 不负责写作 | hub-v1 |

## 项目 ↔ 能力依赖关系

### novel-v1 (小说编辑部)
- **Lead**: lead-novel (选题, 调度, 验收)
- **执行**: story-editor (大纲) → writer (正文) → review-editor (审核)
- **能力需求**: 完整

### research-agent (机会研究)
- **执行**: research-agent (市场扫描, 竞品分析)
- **能力需求**: 完整

### hub-v1 (AI独立站)
- **Lead**: lead-hub (规划, 架构)
- **执行**: tiger-coder, content-manager
- **能力需求**: 完整

### gateway-lite-v1 (模型网关)
- **执行**: tiger-coder
- **能力需求**: 完整

### control-center-v1 (控制平面)
- **执行**: tiger-coder
- **能力需求**: P0 进行中

### routing-layer-v1 (路由层)
- **执行**: tiger-coder
- **能力需求**: P0 进行中

## 关键能力缺口

| 缺口 | 状态 | 优先级 |
|------|------|--------|
| 复杂路由规则引擎 | routing-layer-v1 P0 | P0 |
| 实时健康检查 | preflight-diagnostics-v1 | P1 |
| 证据展示层 | evidence-dashboard-lite-v1 | P1 |

## 能力趋势

| 周期 | 新增能力 | 状态 |
|------|----------|------|
| Week 14 | 能力注册表 | P0 验证中 |
| Week 15 | 路由层规则 | P0 验证中 |
| Week 16 预期 | 控制平面信息层 | P0 进行中 |

---

## 五、数据读取逻辑

```python
# 伪代码

def read_capability_overview():
    # 1. 读取 CAPABILITY-REGISTRY.md
    registry = read_capability_registry()
    
    # 2. 读取 Skills Gap Review
    skills_gap = read_skills_gap_review()
    
    # 3. 构建 Agent 能力列表
    agent_list = []
    for agent in registry.core_agents:
        agent_list.append({
            "agent_id": agent.id,
            "role": agent.role,
            "core_capabilities": agent.capabilities,
            "boundaries": agent.boundaries,
            "supported_projects": agent.supported_projects,
            "key_gap": skills_gap.get_gap(agent.id),
            "related_workflows": agent.related_workflows,
            "related_protocols": agent.related_protocols
        })
    
    # 4. 构建项目依赖关系
    project_deps = {}
    for project in registry.projects:
        project_deps[project.id] = {
            "lead": project.lead,
            "execution": project.agents,
            "capability_status": "完整" / "P0 进行中" / "待启动"
        }
    
    return {
        "agent_count": len(agent_list),
        "agents": agent_list,
        "project_dependencies": project_deps,
        "key_gaps": skills_gap.gaps
    }
```

---

## 六、验收标准

| 标准 | 状态 |
|------|------|
| Founder 能一眼看清核心能力分布 | ✅ |
| 能看到每个 Agent 的职责与边界 | ✅ |
| 能看到关键能力缺口 | ✅ |
| 数据来源清晰，复用 CAPABILITY-REGISTRY | ✅ |
| 可作为后续 Routing/CEO 模块基础 | ✅ |

---

## 七、与 Project Board / Agent Status 的关系

- Capability Overview 补充了能力视角
- Project Board 展示项目，Agent Status 展示执行者，Capability Overview 展示能力
- 三者结合：项目 → Agent → 能力 → 成本

---

## 八、next_step

整合到 Daily Report 18:00 输出中，作为 Gateway Summary 后的第四个模块。
