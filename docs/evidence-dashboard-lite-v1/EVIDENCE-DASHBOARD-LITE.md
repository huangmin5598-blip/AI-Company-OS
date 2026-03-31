# Evidence Dashboard Lite V1 — P1 Lite 方案

**版本**: 1.0
**更新时间**: 2026-03-31
**状态**: P1 启动

---

## 一、项目定位

**目的**：把 AI Company OS 的底层证据翻译成外部一眼能看懂的展示层

**服务对象**：
- GitHub 访客
- 独立站浏览者
- 社媒关注者
- 潜在合作方
- 投资人

---

## 二、P1 Lite 目标

让外部访客一眼看懂：
- 系统在运行
- 资产在增长
- 机制在工作

---

## 三、数据源要求

**复用现有数据**，不新造平行数据层：

| 数据源 | 用途 |
|--------|------|
| TASK-POOL.md | Project Board 外显版 |
| execution-records.json | Agent Status / Run Flow 外显版 |
| gateway-lite/daily/*.json | Gateway Summary 外显版 |
| CAPABILITY-REGISTRY.md | Agent 能力展示 |
| novel-v1/manuscripts/* | 资产增长展示 |

---

## 四、P1 Lite 模块

### 1. Project Board（外显版）

**目标**：展示当前运行的项目

**输出格式**：
```markdown
## 运行中的项目

| 项目 | 阶段 | 状态 |
|------|------|------|
| 小说编辑部 | ITERATION | 🟢 活跃 |
| 机会研究 | ACTIVE | 🟢 活跃 |
| AI 独立站 | MVP | 🟢 活跃 |
| 模型网关 | ACTIVE | 🟢 活跃 |
| 控制平面 | P0 | 🟢 完成 |
```

**数据来源**：TASK-POOL.md Project Registry

---

### 2. Agent Status（外显版）

**目标**：展示核心 Agent 能力

**输出格式**：
```markdown
## AI 团队

| Agent | 角色 | 能力 |
|-------|------|------|
| lead-novel | 项目主管 | 选题, 调度, 验收 |
| writer | 写手 | 正文写作 |
| review-editor | 审核 | 质量控制 |
| research-agent | 侦察兵 | 市场研究 |
| tiger-coder | 开发者 | 系统开发 |
```

**数据来源**：CAPABILITY-REGISTRY.md

---

### 3. Run Flow（外显版）

**目标**：展示任务流转机制

**输出格式**：
```markdown
## 任务流转示例：小说生产

```
lead-novel (选题) 
  → story-editor (大纲)
    → writer (正文)
      → review-editor (审核)
        → 导出 docx
```

**今日产出**：2 篇

**数据来源**：execution-records.json

---

### 4. Asset Growth（外显版）

**目标**：展示资产增长

**输出格式**：
```markdown
## 资产增长

| 类型 | 数量 | 增长趋势 |
|------|------|----------|
| 小说 | 24 篇 | 📈 +2/天 |
| Opportunity Cards | 15 张 | 📈 3/周 |
| 代码模块 | 8 个 | 📈 持续 |

**本月新增**：
- novel-v1: 24 篇
- research-agent: 15 cards
- gateway-lite-v1: 成本记录
- control-center-v1: 7 模块
```

**数据来源**：novel-v1/manuscripts, opportunity-cards

---

### 5. Gateway Summary（外显版）

**目标**：展示成本与治理

**输出格式**：
```markdown
## 成本治理

**今日成本**：$0.00255
**本周成本**：$0.01785

**Fallback**：本周 2 次（已恢复）

**数据来源**：gateway-lite/daily/*.json

---

## 五、输出形式

### 静态页面形式

**Markdown 版**：可用于 GitHub README、文档站

**截图/录屏版**：可用于社媒、PPT

### 不做

- ❌ 实时 Web Dashboard
- ❌ 重交互界面
- ❌ 用户登录系统
- ❌ 复杂数据可视化

### 只做

- ✅ 可复制的 Markdown
- ✅ 可截图的静态展示
- ✅ 可录屏的流程动画

---

## 六、实现路径

### 步骤 1：生成外显版 Markdown

产出文件：
- `evidence/project-board.md`
- `evidence/agent-status.md`
- `evidence/run-flow.md`
- `evidence/asset-growth.md`
- `evidence/gateway-summary.md`

### 步骤 2：整合为单页

产出文件：
- `AI-COMPANY-OS-EVIDENCE.md`

### 步骤 3：同步到外部

- GitHub README
- 独立站证据页
- 社媒内容素材

---

## 七、验收标准

| 标准 | 状态 |
|------|------|
| 外部访客一眼看懂系统在运行 | ✅ |
| 资产增长可见 | ✅ |
| 机制工作可追溯 | ✅ |
| 复用现有数据，不新造数据层 | ✅ |
| 可截图/录屏/发布 | ✅ |

---

## 八、与 control-center-v1 的关系

| control-center-v1 (内) | evidence-dashboard-lite-v1 (外) |
|-----------------------|--------------------------------|
| 完整 7 模块 | 精简 5 模块 |
| 详细数据 | 摘要数据 |
| 内部视角 | 外部视角 |
| Daily/Weekly Report | 可发布展示 |

---

## 九、Registry 字段

| 字段 | 值 |
|------|-----|
| current_stage | P1 |
| next_stage | P2 |
| owner | tiger |
| end_state | 外显版证据页面，可发布到 GitHub/独立站 |
| freeze_rule | P1 完成后才能进入 P2 |

---

## 十、next_step

1. 生成 5 个外显版 Markdown 文件
2. 整合为单页 `AI-COMPANY-OS-EVIDENCE.md`
3. 同步到 GitHub README
