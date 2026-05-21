# AI Company Model - 新增模块方案 (v2)

## 一、Research Agent 方案

### 1.1 Agent 定位

**类型**: Shared Capability Agent  
**定位**: 不属于任何单一项目，为整个 AI Company Model 提供研究能力

### 1.2 职责边界

| 负责 | 不负责 |
|------|--------|
| 市场研究 | 创建项目 |
| 趋势监测 | 分配资源 |
| 机会扫描 | 执行项目任务 |
| 竞品分析 | 做项目决策 |
| 平台变化观察 | 项目管理 |

### 1.3 与 lead-novel 的边界

| Agent | 职责 |
|-------|------|
| **Research Agent** | 趋势、机会、竞品、平台研究 |
| **lead-novel** | 每日选题、story task card、编辑部节奏、验收与复盘 |

### 1.4 运行模式（第一阶段）

- **请求式**: CEO 发起 → Research 执行 → 输出报告
- **周简报**: 每周五输出一次趋势简报
- **不做**: 高频自动监测

### 1.5 输出格式

```
Research Brief / Trend Summary / Opportunity Report

- Research Question
- Research Scope
- Key Findings
- Market Signals
- Recommended Actions
- Impact on Current Projects
```

### 1.6 汇报关系

```
Research Agent → CEO Agent
        ↓
   (同时发送给 Project Lead)
```

### 1.7 标准调用模板

```
【调用关系】
- 调用者: CEO Agent / Project Lead
- 被调用者: Research Agent
- 输出发送: CEO Agent + 发起请求的 Project Lead

【输入】
- Research Request (CEO/Project Lead 发起)
- 可选: Context/Background

【输出】
- Research Brief / Trend Summary / Opportunity Report
```

---

## 二、novel-v1 方案

### 2.1 Agent 配置

| Agent | 角色 | 模型 | 职责 |
|-------|------|------|------|
| lead-novel | Project Lead | MiniMax-M2.5 | 选题决策、任务派发、产出验收 |
| story-editor | Editor | qwen3-vl:8b (本地) | 生成小说大纲 |
| writer | Writer | deepseek-r1:8b (本地) | 根据大纲生成正文 |
| review-editor | Reviewer | qwen3-vl:8b (本地) | 最终审核+版权检查 |

### 2.2 组织结构

```
Founder
   ↓
CEO Agent
   ↓
lead-novel (Project Lead)
   ├ story-editor
   ├ writer
   └ review-editor
```

### 2.3 生产流程（第一阶段）

```
lead-novel (选题)
   ↓
story-editor (大纲: 1000-1500字)
   ↓
writer (正文: 8000-20000字)
   ↓
review-editor (审核+版权)
   ↓
lead-novel (产出验收)
```

### 2.4 长文本 Context Handoff 规则

| 传递 | 不传递 |
|------|--------|
| story-editor → writer: 大纲全文 | writer 不读取 research 原文 |
| writer → review-editor: 最终稿 + 大纲 + task card | review-editor 不读取中间版本 |
| 每一环只传**必要上下文** | 避免**全量透传** |

### 2.5 失败回流机制

| 场景 | 处理方式 |
|------|----------|
| review 不通过 | 退回 writer → revision |
| 第一阶段上限 | 最多 **1 次 revision** |
| 第二次仍不通过 | 标记 **BLOCKED** |
| 记录 | lead-novel 记录 **Issue Log** |

### 2.6 第一阶段验证指标

| 指标 | 定义 |
|------|------|
| **链路完成率** | 成功走完全流程的任务数 / 总任务数 |
| **完整稿产出率** | 产出可投稿版本的任务数 / 总任务数 |
| **Review 打回率** | 被要求 revision 的任务数 / 总任务数 |
| **平均产出时长** | 从选题到 Final Manuscript 的平均耗时 |
| **可投稿率** | 最终通过审核的任务数 / 总任务数 |

---

## 三、版权保护机制（第一阶段）

### 3.1 规则前置

**Prompt Policy 红线规则**:

```markdown
## 允许
- 使用常见题材母题（先婚后爱、替身文学、重生复仇）
- 使用通用类型风格（现代言情、都市情感）
- 原创角色和情节

## 禁止
- 模仿具体小说作品
- 模仿具体作者文风
- 借用知名 IP 世界观
- 使用与知名作品相似的角色/公司/学校名字
```

### 3.2 审核兜底

- review-editor 负责最终版权风险审核
- 选题限制为通用题材母题
- writer 只基于大纲创作，不参考具体作品

---

## 四、openclaw.json 配置

### 4.1 新增 Agents

```json
{
  "id": "research-agent",
  "name": "research-agent",
  "workspace": "~/.openclaw/workspace-research-agent",
  "model": "minimax-cn/MiniMax-M2.5"
},
{
  "id": "lead-novel",
  "name": "lead-novel",
  "workspace": "~/.openclaw/workspace-lead-novel",
  "model": "minimax-cn/MiniMax-M2.5",
  "subagents": {
    "allowAgents": ["story-editor", "writer", "review-editor"]
  }
},
{
  "id": "story-editor",
  "name": "story-editor",
  "workspace": "~/.openclaw/workspace-story-editor",
  "model": "ollama/qwen3-vl:8b"
},
{
  "id": "writer",
  "name": "writer",
  "workspace": "~/.openclaw/workspace-writer",
  "model": "ollama/deepseek-r1:8b"
},
{
  "id": "review-editor",
  "name": "review-editor",
  "workspace": "~/.openclaw/workspace-review-editor",
  "model": "ollama/qwen3-vl:8b"
}
```

### 4.2 更新 main allowAgents

```json
"main" -> allowAgents: [
  "lead-hub",
  "lead-sticker", 
  "tiger-coder",
  "research-agent",
  "lead-novel"
]
```

---

## 五、第一阶段目标

| 目标 | 说明 |
|------|------|
| 跑通 1 篇完整流程 | 选题 → 大纲 → 正文 → 审核 |
| 验证 Agent 协作稳定性 | 上下文不串台 |
| 验证内容生产链路 | 各环节产出正确 |
| 验证投稿流程 | 最终产出可投稿 |

---

## 六、待创建文件清单

### Research Agent

- `workspace-research-agent/AGENTS.md`
- `workspace-research-agent/SOUL.md`

### novel-v1

- `workspace-lead-novel/AGENTS.md`
- `workspace-lead-novel/SOUL.md`
- `workspace-lead-novel/PROJECT.md`
- `workspace-lead-novel/workflow.md`
- `workspace-story-editor/AGENTS.md` + `SOUL.md`
- `workspace-writer/AGENTS.md` + `SOUL.md`
- `workspace-review-editor/AGENTS.md` + `SOUL.md`

---

**方案已完善，是否可以开始执行配置？**
