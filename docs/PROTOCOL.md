# AI Company Model - 系统运行协议

**版本**：1.1  
**状态**：实验阶段  
**最后更新**：2026-03-15

---

## 一、系统组织结构

```
Founder
   ↓
CEO Agent (main - controller)
   ↓
Project Lead Layer
   ├ lead-hub（独立站项目 - Planner）
   └ lead-sticker（表情包项目 - Planner）
   ↓
Execution Layer
   └ tiger-coder（研发执行 Agent）
```

**核心原则**：任务流和信息流都不能越级。

---

## 二、分层职责

### CEO Layer (main - Controller)
- 任务接收与派发
- 进度监督
- 风险预警
- **runtime 编排**：持有 sessions_spawn，唯一实际调用执行层的 controller
- **组织职责**：不直接承担执行层决策

### Project Lead Layer (Planner)
- 项目目标管理
- 任务拆分（生成任务卡）
- 验收建议
- 项目层判断与汇总
- **不直接执行**：不自己修改代码，不自己派发任务给执行层

### Execution Layer
- 执行任务（根据任务卡）
- 输出交付物
- 返回结果
- **不做决策**：只执行 CEO 派发的任务

---

## 三、Runtime 配置

### main (CEO) allowAgents
- lead-hub
- lead-motionclean
- lead-novel
- lead-sticker
- research-agent
- review-editor
- story-editor
- tiger-coder
- writer

### 统一数据源（Single Source of Truth）
- TASK-POOL.md: `/Users/tangbomao/.openclaw/workspace/TASK-POOL.md`
- Execution Records: `/Users/tangbomao/.openclaw/workspace/memory/execution-records.json`

> ⚠️ 所有 agent 必须从统一路径读写，禁止各自猜路径

### 重要说明
tiger-coder 加入 main 的 allowAgents，**仅用于 runtime 编排**，不代表 CEO 越级承担执行层职责。

---

## 四、运行模型（正式）

```
Founder → CEO(main/controller) → Project Lead → CEO(main/controller) → tiger-coder
```

### 步骤：
1. Founder 向 CEO 派发任务
2. CEO 调用 Project Lead 进行任务拆解
3. Project Lead 生成任务卡，回复 CEO
4. CEO 根据任务卡调用 tiger-coder 执行
5. tiger-coder 执行完成，结果返回 CEO
6. CEO 将结果交给对应 Project Lead 做项目层验收与汇总
7. Project Lead 向 CEO 汇报结果

---

## 五、绝对禁止

| 角色 | 禁止行为 |
|------|----------|
| CEO | 在组织层面越级承担执行层职责 |
| Project Lead | 自己执行任务、自己修改代码 |
| Project Lead | 调用其他 Project Lead |
| Execution Agent | 发起任务、做决策 |

---

## 六、任务流

```
Founder → CEO → Project Lead → CEO → Execution Agent
```

**禁止**：跳层执行

---

## 七、信息流

```
Execution Agent → Project Lead → CEO → Founder
```

**禁止**：越级汇报

---

## 八、异常处理

- 任务失败 → Project Lead 记录 Issue Log
- 系统问题 → CEO 在 Build Log 中分析
- 违反结构 → 立即修复

---

## 九、新增 Project Lead 规范

新增 Project Lead 时，必须具备：
1. 项目级 workspace
2. AGENTS.md（定义 Planner 角色）
3. SOUL.md（定义行为风格）
4. PROJECT.md（项目目标与状态）
5. workflow.md（任务拆解流程）
6. **不能有** sessions_spawn 工具（由 CEO 统一调度）

---

*本协议是系统运行的根本准则，所有 Agent 必须遵守。*
