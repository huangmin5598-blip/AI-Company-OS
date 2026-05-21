# Capability Registry — AI Company OS

**版本**: 1.2 (真实运行版)
**更新时间**: 2026-03-31
**状态**: P0 - 验证中

---

## Agent Capability Map

### Core Agents (真实数据)

| agent_id | role | capabilities | boundaries | supported_projects | related_workflows | related_protocols | status |
|----------|------|--------------|------------|-------------------|------------------|--------------------|--------|
| main (tiger) | CEO助手 | 任务分发, 决策支持, 项目管理, 调度 | 不参与具体写作/开发 | 全项目 | heartbeat, dispatch | Decision Protocol | active |
| lead-novel | 项目Lead | 选题生成, Task Card 创建, 任务调度, 验收 | 不负责正文写作, 不负责审核 | novel-v1 | novel-daily, novel-weekly | Task Card Protocol | active |
| story-editor | 结构设计 | 大纲生成, 章节规划, 结构审核, 反馈 | 不负责正文写作, 不负责审核 | novel-v1 | novel-daily | Outline Protocol | active |
| writer | 内容生产 | 正文写作, 场景描写, 对话创作, 细纲 | 不负责审核, 不负责校对 | novel-v1 | novel-daily | Writing Protocol | active |
| review-editor | 质量控制 | 内容审核, 质量评估, PASS/REVISION | 不负责写作 | novel-v1 | novel-daily | Review Protocol | active |
| research-agent | 机会研究 | 市场扫描, 竞品分析, 机会识别, 报告生成 | 不负责项目执行 | research-agent | weekly-research | OS Radar Protocol | active |
| finance-analyst | 金融分析 | 财务报表分析, 投资建议, A股分析 | 不负责投资决策 | finance-ops | daily-brief | Financial Protocol | active |
| tiger-coder | 系统开发 | 代码编写, 方案设计, 系统架构 | 不负责业务逻辑 | gateway-lite, control-center, routing-layer | system-build | - | active |

### System Agents

| agent_id | role | capabilities | boundaries | supported_projects |
|----------|------|--------------|------------|--------------------|
| content-manager | 内容管理 | 内容规划, 发布管理 | 不负责写作 | hub-v1 |

---

## 真实引用案例

### 案例 1: novel-v1 项目分配 (2026-03-31)

**触发**: novel-v1 新任务分配
**引用**: capability-registry-v1
**过程**:
1. CEO 收到任务 → 查 CAPABILITY-REGISTRY
2. 确认 lead-novel 有"选题生成, 任务调度"能力 → 指派 lead-novel
3. lead-novel 调度 story-editor → 查 Capability 确认"大纲生成"能力
4. story-editor 完成后调度 writer → 查 Capability 确认"正文写作"能力

**结论**: Capability Registry 已参与项目分配决策

---

### 案例 2: Skills Gap Review 引用 (2026-03-30)

**触发**: WEEK-14 Skills Gap Review
**引用**: capability-registry-v1
**过程**:
1. 检查现有 Agent 能力
2. 对比需求缺口
3. 明确 lead-novel 的 boundaries（不负责正文写作）

**结论**: Capability Registry 已参与 Skills Gap 分析

---

## Project Capability Map

| project_id | project_name | core_agents | capabilities | stage |
|------------|--------------|--------------|--------------|-------|
| novel-v1 | 小说编辑部 | lead-novel, story-editor, writer, review-editor | 短篇小说生产, 每日2篇, 每周14篇 | ITERATION |
| research-agent | 机会研究 | research-agent | 每周3个Opportunity Card | ACTIVE |
| hub-v1 | AI独立站 | lead-hub | 独立站搭建 | MVP |
| sticker-v1 | 表情包工具 | lead-sticker | 工具开发 | MVP |
| gateway-lite-v1 | 模型网关 | tiger-coder | 成本治理, fallback记录 | ACTIVE |
| control-center-v1 | 控制平面 | tiger-coder | Project Board, Agent Status, System Health | P0 |
| capability-registry-v1 | 能力注册表 | tiger-coder | Agent/Project 能力地图 | P0 |
| routing-layer-v1 | 路由层 | tiger-coder | 流程治理, 任务交通规则 | P0 |

---

## Capability to Project Index

| Capability | Project(s) | Agent(s) |
|------------|------------|----------|
| 短篇小说生产 | novel-v1 | lead-novel → story-editor → writer → review-editor |
| 机会研究 | research-agent | research-agent |
| 独立站搭建 | hub-v1 | lead-hub → tiger-coder |
| 表情包工具 | sticker-v1 | lead-sticker → tiger-coder |
| 成本治理 | gateway-lite-v1 | tiger-coder |
| 控制平面 | control-center-v1 | tiger-coder |
| 能力地图 | capability-registry-v1 | tiger-coder |
| 流程治理 | routing-layer-v1 | tiger-coder |

---

## Boundary Rules

1. **Lead Agent 不做执行**：Lead 只负责规划、调度、验收，不参与具体写作/开发
2. **Writer 不做审核**：写作与审核分离，由 review-editor 负责
3. **System Agent 不做业务**：tiger-coder 只做系统级开发，不做业务内容生产
4. **所有 Agent 必须通过 Heartbeat 调度**：不接受独立 cron 调用（外部信息任务除外）
5. **Task 完成必须写 Registry**：所有 task_completed_event 必须写入 execution-records.json

---

## Registry 字段

| 项目 | current_stage | next_stage | owner | end_state | freeze_rule |
|------|---------------|------------|-------|-----------|-------------|
| capability-registry-v1 | P0 | P1 | tiger | 完整 Agent/Project 能力地图，联动 routing-layer | 完成 P1 前不冻结 |
| routing-layer-v1 | P0 | P1 | tiger | 显式规则完整，联动 control-center 展示 | 完成 P1 前不冻结 |

---

## next_step

- 继续填充边缘 Agent 数据
- 验证更多真实引用案例
- 与 routing-layer-v1 联动验证
