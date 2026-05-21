# 🤖 Agent Status — AI Company OS

**Version**: 1.0 (External Preview)
**Updated**: 2026-04-01
**Purpose**: External display / GitHub / Landing page

---

## 当前 Agent 总览

| # | Agent | Role | Status | Last Active | Model |
|---|-------|------|--------|-------------|-------|
| 1 | main | CEO 助手 | 🟢 idle | 2026-04-01 14:00 | MiniMax-M2.5 |
| 2 | lead-novel | 项目 Lead | 🟢 idle | 2026-04-01 08:00 | MiniMax-M2.5 |
| 3 | story-editor | 结构设计 | 🟢 idle | 2026-04-01 08:00 | MiniMax-M2.5 |
| 4 | writer | 内容生产 | 🟢 idle | 2026-04-01 08:11 | MiniMax-M2.5 |
| 5 | review-editor | 质量控制 | 🟢 idle | 2026-04-01 08:00 | MiniMax-M2.5 |
| 6 | research-agent | 机会研究 | 🟢 idle | 2026-04-01 06:00 | MiniMax-M2.5 |
| 7 | tiger-coder | 系统开发 | 🟡 working | 2026-04-01 14:05 | MiniMax-M2.5 |
| 8 | finance-analyst | 金融分析 | 🟢 idle | 2026-03-30 19:05 | MiniMax-M2.5 |
| 9 | lead-hub | 项目 Lead | 🟢 idle | 2026-03-16 | MiniMax-M2.5 |
| 10 | lead-sticker | 项目 Lead | 🟢 idle | 2026-03-16 | MiniMax-M2.5 |
| 11 | content-manager | 内容管理 | 🟢 idle | - | MiniMax-M2.5 |
| 12 | amazon-seller | 亚马逊卖家 | 🟢 idle | - | Qwen-plus |
| 13 | lead-motionclean | 项目 Lead | 🟢 idle | 2026-03-20 | MiniMax-M2.5 |
| 14 | course-builder | 课程构建 | 🟢 idle | - | MiniMax-M2.5 |

---

## 统计摘要

| 指标 | 值 |
|------|-----|
| **总计 Agents** | 14 |
| **工作中** | 1 (tiger-coder) |
| **空闲** | 13 |
| **阻塞** | 0 |
| **错误** | 0 |

---

## Agent 角色分布

### Core Agents (7)

| Agent | Role | Capabilities | Boundaries |
|-------|------|--------------|------------|
| main | CEO 助手 | 任务分发, 决策支持, 项目管理, 调度 | 不参与具体写作/开发 |
| lead-novel | 项目 Lead | 选题生成, Task Card 创建, 任务调度, 验收 | 不负责正文写作, 不负责审核 |
| story-editor | 结构设计 | 大纲生成, 章节规划, 结构审核, 反馈 | 不负责正文写作, 不负责审核 |
| writer | 内容生产 | 正文写作, 场景描写, 对话创作, 细纲 | 不负责审核, 不负责校对 |
| review-editor | 质量控制 | 内容审核, 质量评估, PASS/REVISION | 不负责写作 |
| research-agent | 机会研究 | 市场扫描, 竞品分析, 机会识别, 报告生成 | 不负责项目执行 |
| finance-analyst | 金融分析 | 财务报表分析, 投资建议, A股分析 | 不负责投资决策 |

### System Agents (1)

| Agent | Role | Capabilities | Boundaries |
|-------|------|--------------|------------|
| tiger-coder | 系统开发 | 代码编写, 方案设计, 系统架构 | 不负责业务逻辑 |

### Project Leads (6)

| Agent | Project | Stage |
|-------|---------|-------|
| lead-hub | hub-v1 | MVP |
| lead-sticker | sticker-v1 | MVP |
| lead-motionclean | motionclean-v1 | MVP |
| content-manager | hub-v1 | - |
| amazon-seller | amazon | - |
| course-builder | course | - |

---

## 模型使用分布

| 模型 | Agents |
|------|--------|
| MiniMax-M2.5 | 12 |
| Qwen-plus | 1 (amazon-seller) |

---

## 项目关联

| Project | Core Agents |
|---------|-------------|
| novel-v1 | lead-novel → story-editor → writer → review-editor |
| research-agent | research-agent |
| hub-v1 | lead-hub → content-manager → tiger-coder |
| sticker-v1 | lead-sticker → tiger-coder |
| finance-ops | finance-analyst |
| control-center | tiger-coder |
| gateway-lite | tiger-coder |

---

## 数据来源

- `openclaw agents list` → Agent 列表、模型、配置
- `CAPABILITY-REGISTRY.md` → Agent 能力定义
- execution-records → 执行记录

---

*Generated: 2026-04-01 04:07 (Asia/Shanghai)*