# AI Company Model - 新增模块方案 (v3)

---

## 一、第一阶段目标（更新）

| 目标 | 说明 |
|------|------|
| 跑通 1 篇完整生产链 | 选题 → 大纲 → 正文 → 审核 |
| 验证协作稳定性 | 上下文不串台 |
| 验证是否产出可投稿稿件 | 不验证真实投稿闭环 |

---

## 二、lead-novel 验收口径（新增）

### 2.1 对 story-editor 的验收

| 验收项 | 标准 |
|--------|------|
| 核心设定清晰 | 世界观、核心冲突明确 |
| 人物关系明确 | 主要角色及其关系清晰 |
| 情绪线成立 | 有起伏设计 |
| 结构完整 | 有章节规划 |
| 可扩展性 | 可支持 8000–20000 字展开 |

### 2.2 对 writer 的验收

| 验收项 | 标准 |
|--------|------|
| 正文完整 | 无章节缺失 |
| 无明显断裂 | 情节连贯 |
| 情绪推进成立 | 有起伏、高潮 |
| 可进入 review | 达到基本完成度 |

### 2.3 对 review-editor 的验收

| 验收项 | 标准 |
|--------|------|
| 输出格式 | 必须给出 PASS / REVISION REQUIRED / BLOCKED |
| 问题具体 | 指出具体问题，不允许空泛评价 |
| 版权检查 | 包含版权风险评估 |

---

## 三、Research Agent 输入优先级（新增）

| 优先级 | 来源 | 说明 |
|--------|------|------|
| **第一** | CEO 主动发起 | 战略级研究需求 |
| **第二** | lead-hub / lead-novel / lead-sticker | 项目层选题研究 |
| **第三** | 每周趋势简报 | 周五自动输出 |

**限制**: 避免 Research 什么都研究，结果没有决策价值。

---

## 四、版权保护机制（更新为两层）

### 4.1 前置层（红线条约束）

在 **story task card** 和 **story-editor** 阶段加入：

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

### 4.2 审核层

- review-editor 做最终版权与高混淆风险检查

---

## 五、Runtime 层与组织层区分（更新）

### 5.1 组织层

```
CEO (main)
   ↓
research-agent
   ↓
lead-novel
```

- CEO 只对接 research-agent 和 lead-novel
- CEO 不直接承担执行层职责
- lead-novel 是 novel-v1 项目负责人

### 5.2 Runtime 层（当前阶段运行模型）

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

**说明**:
- Project Lead 当前不适合作为 sub-controller
- main 作为唯一 controller 需要具备 spawn 所有编辑部 Agent 的能力
- 不要把"allowAgents"只按组织层限制

### 5.3 openclaw.json 配置

```json
{
  "id": "main",
  "subagents": {
    "allowAgents": [
      "lead-hub",
      "lead-sticker",
      "tiger-coder",
      "research-agent",
      "lead-novel",
      "story-editor",
      "writer",
      "review-editor"
    ]
  }
}
```

---

## 六、失败回流机制（保持）

| 场景 | 处理 |
|------|------|
| review 不通过 | 退回 writer → revision |
| 第一阶段上限 | 1 次 revision |
| 第二次仍不通过 | 标记 BLOCKED |
| 记录 | lead-novel 记录 Issue Log |

---

## 七、第一阶段验证指标（保持）

| 指标 | 定义 |
|------|------|
| 链路完成率 | 成功走完全流程的任务数 / 总任务数 |
| 完整稿产出率 | 产出可投稿版本的任务数 / 总任务数 |
| Review 打回率 | 被要求 revision 的任务数 / 总任务数 |
| 平均产出时长 | 从选题到 Final Manuscript 的平均耗时 |
| 可投稿率 | 最终通过审核的任务数 / 总任务数 |

---

**方案已按 5 点反馈更新，确认后开始执行配置。**
