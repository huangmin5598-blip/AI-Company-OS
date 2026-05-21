# AI Company Model Build Log 04

## Novel Editorial Department + Research Agent Architecture

---

### Background

**Purpose**: Verify the novel editorial department architecture with Research Agent integration.

Based on NOVEL-V1-PLAN-V3.md, this experiment validates:
- Novel editorial workflow: **选题 → 大纲 → 正文 → 审核**
- Research Agent positioning and input priority
- Multi-agent collaboration stability

---

### Architecture Design

#### Organizational Structure

```
CEO (main)
   ↓
research-agent (Shared Capability)
   ↓
lead-novel (Project Lead)
   ↓
Editorial Department
   ├ story-editor (大纲生成)
   ├ writer (正文创作)
   └ review-editor (审核+版权)
```

#### Runtime Flow

```
Founder
   ↓
CEO (main / controller)
   ↓
lead-novel (项目层判断与验收)
   ↓
CEO spawn → story-editor
   ↓
CEO spawn → writer
   ↓
CEO spawn → review-editor
   ↓
结果回 lead-novel 做项目层判断
```

#### Research Agent Input Priority

| 优先级 | 来源 | 说明 |
|--------|------|------|
| **第一** | CEO 主动发起 | 战略级研究需求 |
| **第二** | lead-hub / lead-novel / lead-sticker | 项目层选题研究 |
| **第三** | 每周趋势简报 | 周五自动输出 |

---

### Agent Specifications

| Agent | Role | Model | Function |
|-------|------|-------|----------|
| research-agent | Research | qwen3:14b | 趋势研究、选题调研 |
| lead-novel | Project Lead | - | novel-v1 负责人 |
| story-editor | Editor | qwen3-vl:8b | 生成小说大纲 (1000-1500字) |
| writer | Writer | deepseek-r1:8b | 生成正文 (8000-20000字) |
| review-editor | Reviewer | qwen3-vl:8b | 审核+版权检查 |

---

### Validation Criteria

#### Story Editor 验收标准

| 验收项 | 标准 |
|--------|------|
| 核心设定清晰 | 世界观、核心冲突明确 |
| 人物关系明确 | 主要角色及其关系清晰 |
| 情绪线成立 | 有起伏设计 |
| 结构完整 | 有章节规划 |
| 可扩展性 | 可支持 8000–20000 字展开 |

#### Writer 验收标准

| 验收项 | 标准 |
|--------|------|
| 正文完整 | 无章节缺失 |
| 无明显断裂 | 情节连贯 |
| 情绪推进成立 | 有起伏、高潮 |
| 可进入 review | 达到基本完成度 |

#### Review Editor 验收标准

| 验收项 | 标准 |
|--------|------|
| 输出格式 | 必须给出 PASS / REVISION REQUIRED / BLOCKED |
| 问题具体 | 指出具体问题，不允许空泛评价 |
| 版权检查 | 包含版权风险评估 |

---

### Copyright Protection Mechanism

#### Layer 1: Pre-check (Red Lines)

In **story task card** and **story-editor** stage:

```markdown
## 版权红线（禁止）

- 不模仿明确作品设定
- 不复刻已知角色关系
- 不沿用知名 IP 世界观
- 不贴近具体作品桥段结构

## 名字生成规则

- 使用原创名字
- 避免与知名作品角色重名
```

#### Layer 2: Review Check

- review-editor 做最终版权与高混淆风险检查

---

### Fallback Mechanism

| 场景 | 处理 |
|------|------|
| review 不通过 | 退回 writer → revision |
| 第一阶段上限 | 1 次 revision |
| 第二次仍不通过 | 标记 BLOCKED |
| 记录 | lead-novel 记录 Issue Log |

---

### Metrics (Phase 1)

| 指标 | 定义 |
|------|------|
| 链路完成率 | 成功走完全流程的任务数 / 总任务数 |
| 完整稿产出率 | 产出可投稿版本的任务数 / 总任务数 |
| Review 打回率 | 被要求 revision 的任务数 / 总任务数 |
| 平均产出时长 | 从选题到 Final Manuscript 的平均耗时 |
| 可投稿率 | 最终通过审核的任务数 / 总任务数 |

---

### Experiment Status

| Component | Status |
|-----------|--------|
| Architecture Design | ✅ Complete |
| Agent Definitions | ✅ Complete |
| Workflow Design | ✅ Complete |
| Validation Criteria | ✅ Complete |
| Runtime Execution | ⏳ Pending |

---

### System Status

| Capability | Status |
|------------|--------|
| Architecture Alignment | ✅ |
| Runtime Stability | ✅ |
| Multi-project Execution | ✅ |
| Project Lead Review | ✅ |
| Novel Editorial Workflow | 🔄 Designed |
| Research Agent Integration | 🔄 Designed |

---

### Next Steps

1. Configure agents in openclaw.json
2. Set up workspaces for each editorial agent
3. Run first production test: single story complete flow
4. Validate collaboration stability

---

### Log Metadata

- **Log Generated**: 2026-03-18
- **Experiment**: 04
- **Architecture**: Novel Editorial Department + Research Agent
- **Status**: DESIGN COMPLETE ✅ (Runtime pending)
