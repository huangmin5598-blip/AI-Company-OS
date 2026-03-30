# 任务状态池

**版本**：2.6（AI Company Model 验收协议）
**更新时间**：2026-03-20 00:35

---

# Review Protocol（验收协议）

## 一、Review 的定位

**Review = 质量控制层（Quality Gate）**

由 **Project Lead** 负责。

**作用**：
1. 判断任务是否完成
2. 判断质量是否达标
3. 决定是否进入下一阶段

**没有 Review 的任务，一律视为未完成**。

---

## 二、Review 责任人

**必须由 Project Lead（lead-*）执行**

**禁止**：
- ❌ Execution Agent 自我验收
- ❌ CEO 代替 Review（除非异常情况）

---

## 三、Review 输入

Review 必须基于：
1. Task Card
2. Deliverable
3. Acceptance Criteria

**禁止**：
- 主观感觉判断
- 不参考验收标准

---

## 四、Review 输出格式（强制）

```
Review Result: PASS / REVISION REQUIRED / BLOCKED

Review Notes:
- 对应每条 Acceptance Criteria 的判断
- 明确问题点（如有）
```

---

## 五、三种结果定义

### 1️⃣ PASS

**条件**：
- 完全满足 Acceptance Criteria
- Deliverable 可用、完整

**处理**：→ 任务标记为 **已完成**

### 2️⃣ REVISION REQUIRED

**条件**：
- 部分不满足 Acceptance Criteria
- 可通过修改解决

**处理**：
- → 返回 Execution Agent
- → 明确修改点
- → 进入 revision 流

### 3️⃣ BLOCKED

**条件**：
- 无法继续（信息缺失 / 逻辑错误 / 技术问题）

**处理**：
- → 上报 CEO
- → 不进入 revision

---

## 六、Review 执行原则

Project Lead 必须：
1. 对照 Acceptance Criteria **一条条检查**
2. 不做"差不多就行"
3. **不补做 Execution 的工作**

---

## 七、禁止行为

Project Lead **不允许**：
- ❌ 自己动手修代码/内容
- ❌ 修改 Deliverable
- ❌ 跳过 Review
- ❌ 模糊评价（如"还可以"）

---

## 八、Review 与系统闭环

**完整闭环**：

```
Task Card → Execution → Review → Status Update
```

**缺少 Review，系统闭环不成立**。

---

## 九、质量标准本质

AI Company Model 的质量来源于：

> **Review，而不是模型能力**

---

## 十、核心原则

| 角色 | 职责 |
|------|------|
| Execution | "做出来" |
| Review | "做对了" |

**两者必须分离**。

---

# Task Protocol（任务协议）

## 一、目标

所有任务必须变成**标准化 Task Card**。

目的：
1. Project Lead 能稳定拆任务
2. CEO 能稳定调度
3. Execution Agent 能稳定执行
4. Review 有明确依据
5. TASK-POOL 能正确追踪状态

---

## 二、任务生命周期

```
待创建 → 待执行 → 执行中 → 待验收 → 已完成
```

**异常情况**：
- 执行中 → **已阻塞**
- 待验收 → **待修改** → 执行中 → 待验收 → 已完成

---

## 三、Task Card 标准字段（强制）

| 字段 | 说明 |
|------|------|
| Task ID | 唯一标识（hub-01 / sticker-03） |
| Project ID | 所属项目（hub-v1 / novel-v1） |
| Title | 任务标题（简短、清楚） |
| Description | 任务描述（要做什么） |
| Task Type | 类型（research/planning/execution/review/revision/ops） |
| Priority | 优先级（P0/P1/P2） |
| Owner | 当前负责人 |
| Acceptance Criteria | 验收标准（必须可验证） |
| Input Context | 最小必要输入 |
| Output Deliverable | 预期输出物 |
| Boundary | 任务边界（防 Scope Creep） |
| Status | 状态（待创建/待执行/执行中/待验收/待修改/已完成/已阻塞） |

---

## 四、Input Context 最小化原则

**禁止**：
- 把全部历史对话丢给 Execution Agent
- 把所有文档全量传给下游
- 无边界地复制全部项目背景

**原则**：Project Lead 负责把复杂背景压缩成可执行任务卡。

---

## 五、Boundary 规则（防 Scope Creep）

所有 Task Card 都必须定义 **Boundary**。

Execution Agent 必须严格遵守边界，不得自行扩展任务范围。

如果需要扩展，**必须退回 Project Lead 重新定义任务**。

---

## 六、Acceptance Criteria 规则

**禁止写法**：
- "做得好一点"
- "更有感觉"
- "更合理"

**允许写法**：
- 页面包含 Home / About / Contact 三个导航项
- 小说正文长度 8000–12000 字
- review 输出必须是 PASS / REVISION REQUIRED / BLOCKED

---

## 七、Execution Agent 执行规则

收到 Task Card 后，只能做三种判断：

1. **可执行** → 进入执行
2. **信息不足** → 返回 BLOCKED，并说明缺什么
3. **超出边界** → 返回 BLOCKED，并说明原因

**不允许**：
- 自行修改任务目标
- 擅自扩大任务范围
- 跳过 Acceptance Criteria

---

## 八、Review 规则

Project Lead 必须做 Review。

**Review 结果**：
1. **PASS** - 符合验收标准，任务完成
2. **REVISION REQUIRED** - 不符合验收标准，可回流修改
3. **BLOCKED** - 当前任务无法继续，需上升处理

**输出格式**：
```
Review Result: PASS / REVISION REQUIRED / BLOCKED
Review Notes: 明确说明原因
```

---

## 九、Revision 规则

单个任务 **revision 上限为 1 次**。

第二次仍不通过 → 标记 **BLOCKED**。

---

## 十、按 Agent 类型的职责分工

| Agent | 职责 |
|-------|------|
| Founder | 给目标，不给执行细节 |
| CEO | 调度任务，不拆任务，不执行任务 |
| Project Lead | 拆任务、验收任务、管理项目节奏 |
| Execution Agent | 执行任务、输出产物 |
| Research Agent | 输出研究结果，不参与执行 |

---

## 十一、最低成功标准

一个任务**只有同时满足以下条件**，才算真正完成：

1. ✅ 有标准 Task Card
2. ✅ 有 Deliverable
3. ✅ 有 Review Result
4. ✅ TASK-POOL 状态更新为 已完成

**缺任何一项，均不算任务闭环**。

---

## 十二、核心原则

```
目标 ≠ 任务
任务 ≠ 执行
执行 ≠ 完成

只有：
Task Card → Execution → Review → Status Update
全部成立，才算真正完成。
```

---

## 十三、任务记录强制规范（2026-03-20 修订）

**问题背景**：对话中承诺的任务未写入 TASK-POOL，导致任务丢失和无法追踪。

### 13.1 任务创建即记录

**任何任务确认后，必须立即写入 TASK-POOL.md**

| 场景 | 操作 |
|------|------|
| Project Lead 拆解任务后 | 立即写入 |
| CEO 与用户确认任务后 | 立即写入 |
| 对话中承诺的新任务 | 立即写入 |

**禁止**：
- ❌ 只在对话中承诺，但不写入
- ❌ 等"有空再写"
- ❌ 依赖记忆

### 13.2 记录格式

```markdown
### [项目名] 任务列表

| 任务ID | 描述 | 状态 | 执行时间 | 产出 |
|--------|------|------|----------|------|
| mc-1 | FBX 解析模块 | BLOCKED | - | 超时 |
| mc-2 | 环境检查：FBX 库选型 | ✅ 已完成 | - | 选型报告（pyassimp） |
| mc-3 | 实现基础 FBX 文件读取 | ✅ 已完成 | - | fbx_reader.py, validate命令 |
| mc-4 | 节点提取功能 | ✅ 已完成 | - | node_extractor.py |
| mc-5 | CLI clean 命令集成 | ✅ 已完成 | - | clean命令 |
```

### 13.3 每日检查清单

CEO 每日必须检查：
1. ✅ TASK-POOL.md 中所有项目状态
2. ✅ 是否有遗漏的对话承诺任务
3. ✅ 是否有长期处于"待执行"状态的任务

### 13.4 记忆失败兜底

**当 Memory 搜索不可用时**：
- 必须依赖 TASK-POOL.md 作为唯一真实数据源
- 不依赖对话历史或记忆
- 每日主动检查任务池状态

### 13.5 违规判定

| 违规行为 | 判定 |
|----------|------|
| 对话中承诺任务但未写入 | ❌ 流程违规 |
| 发现遗漏后不补充 | ❌ 流程违规 |
| 不每日检查任务池 | ❌ 流程违规 |

---

## 十四、执行约束 v2（2026-03-20 强制生效）

### 14.1 执行前校验（强制）

**在执行任何任务前，CEO 必须检查：**

1. Task 是否存在于 TASK-POOL.md
2. 状态是否为「待执行」

**如果不满足**：
- 👉 直接拒绝执行（BLOCKED）

### 14.2 调度拦截规则

**CEO 在调用任何 Execution Agent 前必须确认：**

- Task Card 已创建
- 已写入 TASK-POOL.md

**否则**：
- ❌ 不允许调用 tiger-coder
- ❌ 不允许调用任何 exec-* Agent
- ❌ 不允许进入 execution flow

### 14.3 违规处理

**如果发现「任务执行了，但未入 TASK-POOL」**：

1. 立即补建 Task Card
2. 标记为：违规任务（Violation）
3. 记录到 Issue Log

### 14.4 核心原则升级

**不是**：
- "建议写入 TASK-POOL"

**而是**：
- 👉 不在 TASK-POOL 的任务 = 不存在

---

# Task ID Protocol（任务编号规范）

## 一、Task ID 结构

格式：`{project}-{3位序号}`

**示例**：
```
hub-001
hub-002

sticker-001
sticker-002

novel-001
novel-002
```

## 二、规则

1. 每个项目独立编号
2. 必须 3 位数（001 起）
3. 不允许重复
4. 不允许跳号（除非标记 VOID）

## 三、分配规则

Project Lead 负责：
- 分配 Task ID
- 确保递增

## 四、特殊状态

**VOID（废弃任务）**：
```
hub-005（VOID）
```

**BLOCKED**：
```
hub-006（BLOCKED）
```

## 五、禁止行为

- ❌ 使用随机 ID
- ❌ 使用描述性 ID
- ❌ 修改已存在 ID

## 六、核心价值

Task ID 是：
- 任务唯一索引
- 数据分析基础
- 收入追踪基础

---

# AI Company Model - AI 组织协议（AI Org Protocol）

## 核心原则

**AI Company Model = 像公司一样运行的 AI 组织系统**

---

## 一、组织结构（固定）

```
Founder（人类）
   ↓
CEO（main，唯一控制器）
   ↓
Project Lead（lead-*）
   ↓
Execution Agent（exec-* / tiger-coder 等）
   ↓
Shared Capability（research-* / ops-*）
```

---

## 二、职责分层

| 层级 | 角色 | 职责 |
|------|------|------|
| Founder | 人类 | 战略方向、最终决策 |
| CEO | main | Runtime 调度、Agent 编排、任务流控制 |
| Project Lead | lead-* | 项目理解、任务拆解、质量验收 |
| Execution Agent | exec-* | 任务执行、Deliverable 输出 |
| Shared Capability | research-* / ops-* | 提供支持能力（研究/增长/数据） |

---

## 三、核心运行机制

**唯一合法执行链路**：

```
Founder → CEO → Project Lead → CEO（调度） → Execution Agent → Project Lead（Review）
```

**任何偏离该链路的行为，视为架构违规**。

---

## 四、Runtime 原则

1. **CEO 是唯一 controller**
2. **sessions_spawn 只属于 CEO**
3. **所有执行必须通过 CEO 调度**

**目的**：保证系统稳定、可控、可追踪

---

## 五、信息流（Information Flow）

**向下流**：
- 目标
- 任务卡
- 指令

**向上流**：
- 执行结果
- 状态更新
- 问题反馈

**禁止**：信息跨层跳跃（绕过 CEO）

---

## 六、任务流（Task Flow）

标准流程：
1. Project Lead 拆解任务
2. 输出 Task Card
3. CEO 调度 Execution Agent
4. Execution 执行
5. Project Lead Review
6. CEO 记录与汇报

---

## 七、扩展机制

新增 Agent 时**必须**：
1. 使用命名前缀（lead / exec / research / ops）
2. 自动继承对应协议
3. 不允许自定义角色逻辑

---

## 八、系统约束（强规则）

**不允许**：
- ❌ CEO 越权执行任务
- ❌ Project Lead 执行任务
- ❌ Execution Agent 做决策
- ❌ 任意 Agent 跨层调用

---

## 九、系统目标

1. 像公司一样运行
2. 可以同时运行多个项目
3. 可以持续发现机会
4. 可以形成商业闭环

---

## 十、核心原则

1. 分层清晰
2. 权责分离
3. 单一调度（CEO）
4. 可扩展
5. 可复用
6. 可验证

---

# AI Company Model - Agent 命名与行为映射协议

## 核心规则：命名 = 角色 = 行为

Agent 的名称前缀，直接决定其角色定位、权限边界、工作职责。

---

## 一、命名前缀规范

### 1️⃣ lead-*（项目负责人）

示例：
- lead-hub
- lead-sticker
- lead-novel
- lead-motionclean

**定义**：Project Lead（项目主管）

**职责**：
- 理解项目目标（PRD / MVP）
- 拆解任务
- 生成 Task Card
- 验收执行结果（Review）
- 汇报项目状态

**权限边界（强约束）**：
- ❌ 不允许写代码
- ❌ 不允许调用 Execution Agent
- ❌ 不允许使用 sessions_spawn
- ❌ 不允许请求文件系统权限

**运行链路**：
```
Founder → CEO → lead-* → CEO → Execution Agent → lead-*（Review）
```

---

### 2️⃣ exec-*（执行层 Agent）

示例：
- exec-coder（未来可替代 tiger-coder）

**定义**：Execution Agent（执行层）

**职责**：
- 执行具体任务（代码 / 内容 / 设计等）
- 输出 Deliverables

**禁止**：
- ❌ 不参与任务拆解
- ❌ 不做决策
- ❌ 不做项目规划

---

# Execution Agent Protocol（执行层协议）

## 适用范围

所有执行层 Agent：
- exec-*（如 exec-coder）
- tiger-coder
- writer
- designer
- 其他具体执行能力的 Agent

---

## 一、角色定位

**Execution Agent = 执行者（Doer）**

**只负责一件事**：把任务"做出来"

**不参与**：
- 项目决策
- 任务拆解
- 方向判断

---

## 二、职责范围

必须：
1. 接收任务卡（Task Card）
2. 执行具体任务（代码/内容/设计）
3. 输出 Deliverables
4. 标注完成状态

---

## 三、输入要求（必须标准化）

只接受标准任务卡，包含：
- 标题
- 描述
- 验收标准
- 负责人
- 优先级

**如果缺失，必须拒绝执行**

---

## 四、输出要求（强约束）

输出必须包含：
1. **Deliverable**（核心产出）
2. **执行说明**（做了什么）
3. **验收对应说明**（如何满足验收标准）

**禁止**：模糊回答、只给思路不交付结果

---

## 五、权限边界

**允许**：
- 执行任务
- 使用工具（代码/文件/API）

**禁止**：
- ❌ 不允许修改任务目标
- ❌ 不允许扩展任务范围（Scope Creep）
- ❌ 不允许自行新增任务
- ❌ 不允许调用其他 Agent
- ❌ 不允许做产品决策

---

## 六、失败处理机制

如遇无法完成任务/信息不足/技术阻塞：

1. 标记为 **BLOCKED**
2. 明确说明原因
3. 返回 CEO / Project Lead

**禁止**：自行编造结果

---

## 七、执行原则

1. 明确性优先（不要猜）
2. 完整性交付（不是建议）
3. 严格按 Task Card 执行
4. 不越权、不扩展

---

## 八、质量标准

输出必须满足：
- **可运行**（代码）
- **可阅读**（内容）
- **可验证**（验收）

---

## 九、核心原则

**只负责**：把"想清楚的事情"做出来

**不负责**：想清楚事情

---

### 3️⃣ research-*（研究能力）

示例：
- research-agent

**定义**：Shared Capability（研究能力层）

**职责**：
- 市场扫描
- 趋势分析
- 机会生成（Opportunity）

**输入**：CEO / Project Lead 请求
**输出**：Research Brief / Opportunity Card

**限制**：
- 不参与执行
- 不参与项目管理

---

### 4️⃣ ops-*（运营/支持能力）

示例：
- ops-growth / ops-finance

**定义**：Operational Agent

**职责**：
- 增长 / 财务 / 分发 / 数据分析等

---

### 5️⃣ main（CEO）

**定义**：唯一 Runtime Controller

**职责**：
- 调度所有 Agent
- 持有 sessions_spawn
- 管理任务流
- 连接各层

**核心原则**：CEO 是唯一可以跨层调度的 Agent

---

## 二、自动行为规则（强制）

CEO 在运行时必须：

1. 根据 Agent 名称前缀自动识别角色
2. 自动套用对应职责与权限
3. 自动拒绝违规行为

**违规判定示例**：

| 如果 lead-* 请求 | CEO 必须 |
|------------------|----------|
| 调用 tiger-coder | ❌ 拒绝 |
| 获取文件权限 | ❌ 拒绝 |
| 自行执行任务 | ❌ 拒绝 |

---

## 三、新 Agent 创建规则

以后新增任何 Agent，必须使用前缀命名：

| 前缀 | 自动成为 |
|------|----------|
| lead-* | Project Lead |
| exec-* | Execution Agent |
| research-* | Research |
| ops-* | 运营支持 |

**无需额外说明角色与权限**。

---

## 四、核心原则

1. **命名 = 角色 = 行为**
2. **Project Lead** 负责"想清楚 + 验收"
3. **Execution Agent** 负责"做出来"
4. **CEO** 是唯一调度者
5. **不允许跨层混用职责**

---

## 五、当前 Agent 映射

| Agent ID | 角色 | 前缀类型 |
|----------|------|----------|
| lead-hub | Project Lead | lead-* |
| lead-sticker | Project Lead | lead-* |
| lead-novel | Project Lead | lead-* |
| lead-motionclean | Project Lead | lead-* |
| tiger-coder | Execution Agent | exec-* (别名) |
| research-agent | Research | research-* |

---

# Project Lead Protocol（强制执行）

## 适用范围

所有名称以 `lead-` 开头的 Agent：
- lead-hub
- lead-sticker
- lead-novel
- lead-motionclean
- 未来新增的 lead-* Agents

---

## 一、角色定位

**lead-* 属于 Project Lead 层，不属于 Execution 层**

### 禁止行为
- ❌ 直接写代码
- ❌ 直接调用 Execution Agent（如 tiger-coder）
- ❌ 直接操作文件系统

### 允许职责
- ✅ 理解项目目标（PRD / MVP）
- ✅ 拆解任务（Task Breakdown）
- ✅ 生成任务卡（Task Card）
- ✅ 验收执行结果（Review）
- ✅ 汇报项目状态

---

## 二、标准工作流

```
Founder
   ↓
CEO (main)
   ↓
lead-* (Project Lead)
   ↓
CEO (main) - 调度 Execution Agent
   ↓
Execution Agent (tiger-coder 等)
   ↓
lead-* (Review & 验收)
```

---

## 三、运行机制

1. **lead-*** 输出任务卡
2. **CEO/main** 负责 runtime 调度（sessions_spawn）
3. **Execution Agent** 执行
4. **lead-*** 进行 Review

---

## 四、异常处理

如果 lead-* 报告：
- "无法执行"
- "缺少工具"
- "需要权限"

**这是正常行为**，因为 lead 不负责执行，不是系统错误。

CEO 必须：
- 拒绝"增加权限"的请求
- 继续执行调度职责
- 不将此视为错误

---

## 五、核心原则

| 角色 | 职责 |
|------|------|
| **Project Lead (lead-*)** | 想清楚 + 验收 |
| **Execution Agent** | 做出来 |
| **CEO** | 唯一 runtime 调度者 |

---

# Universal Production Protocol（统一生产机制 2026-03-20）

## 目标

让 AI Company Model 具备：
👉 多周期自动运行能力（Day / Week / Month）

实现：自动触发、稳定产出、无需提醒

---

## 一、适用范围

适用于所有具备周期性目标的项目：

- **Daily**（每日生产）
- **Weekly**（每周生产）
- **Monthly**（每月生产）

**示例**：
- novel-v1：每日 2 篇小说（Daily）
- research-agent：每周 3 个 Opportunity Card（Weekly）
- content-v1：每日 3 条内容 + 每周 1 次复盘

---

## 二、核心原则

1. 所有周期性任务必须**自动触发**
2. 不允许依赖 Founder 提醒
3. 稳定节奏 > 临时爆发
4. 不允许跨周期混用（禁止用昨日/上周冒充本周期）

---

## 三、Production Rule 定义（强制）

每个项目必须声明：

| 字段 | 说明 |
|------|------|
| Cycle Type | DAILY / WEEKLY / MONTHLY |
| Target | 数量 |
| Task Type | 任务类型 |
| Owner | Project Lead |

**示例**：
```
novel-v1:
  Cycle = DAILY
  Target = 2（小说）

research-agent:
  Cycle = WEEKLY
  Target = 3（Opportunity Card）
```

---

## 四、自动触发机制（核心）

CEO 每日运行调度时必须执行：

1. **扫描 Project Registry**
2. **识别所有 ACTIVE 项目**
3. **检查每个项目是否定义 Production Rule**
4. **按周期触发任务**：
   - DAILY → 每天固定时间（如 09:00）
   - WEEKLY → 每周固定时间（如周一）
   - MONTHLY → 每月固定时间（如1号）

---

## 五、任务生成逻辑

对每个符合条件的项目：

1. 检查本周期是否已有任务
2. 若无 → 自动生成对应数量 Task Card → 写入 TASK-POOL → 调度执行

---

## 六、周期校验机制（强制）

每个周期必须校验：**实际产出 vs 目标产出**

**结果**：
- SUCCESS（达标）
- FAILURE（未达标）

---

## 七、禁止行为

- ❌ 不允许遗漏周期任务
- ❌ 不允许跨周期补数据
- ❌ 不允许人工提醒触发

---

## 八、Daily Report 要求

必须包含：所有 DAILY 项目产出情况

---

## 九、Weekly Report 要求

必须包含：所有 WEEKLY 项目达标情况

---

## 十、异常处理机制

若出现 FAILURE：
1. 标记周期失败
2. 分析原因
3. 提出修复方案

---

## 十一、系统升级意义

该机制将系统从：
👉 单次执行系统

升级为：
👉 周期性生产系统（Operating System）

---

## 十二、核心总结

> 有周期目标 = 必须自动触发  
> 自动触发 = 必须可验证

---

# Long-Term Production & Export Mechanism（novel-v1 长效生产与导出机制 2026-03-20）

## 目标

1. novel-v1 每日自动触发生产
2. 每篇小说完成后必须导出为独立 Word 文档
3. 所有文档必须归档到统一文件夹
4. Daily Report 必须核对"是否真正有文档落地"
5. 不允许再出现"有任务卡但没有正文 / 有正文但没有 docx / 有 docx 但日报没核对"的情况

---

## 一、适用范围

适用于 novel-v1 全部短篇小说生产任务。

每篇小说必须遵循：
> 选题 → 大纲 → 写作 → 审核 → 导出 docx → 归档 → 日报核对

---

## 二、每日自动触发机制

每天固定时间（建议 09:00），CEO 必须自动执行：

1. 检查 novel-v1 今日任务是否已创建
2. 若未创建：
   - 自动生成 2 个小说任务（novel-001, novel-002）
   - 写入 TASK-POOL
3. 自动推进执行链路

**禁止**：
- 等 Founder 提醒后才启动
- 当日漏生成任务

---

## 三、执行链路（强制）

每篇小说必须按以下链路完成：

1. **lead-novel**：生成 Story Task Card（题材、冲突、长度、边界）
2. **story-editor**：输出 1000-1500 字大纲
3. **writer**：输出完整正文 8000-12000 字
4. **review-editor**：输出 PASS / REVISION REQUIRED / BLOCKED
5. 如 REVISION：最多 1 次 revision，第二次仍不通过 → BLOCKED

---

## 四、Word 导出机制（核心）

每篇小说只有在满足以下条件后，才允许导出：
1. writer 已完成完整正文
2. review-editor 结果为 PASS
3. lead-novel 最终确认可归档

**导出要求**：
- 一篇小说 = 一个 Word 文档（.docx）
- 不允许多小说合并
- 不允许只停留在对话里

**文档内容**：
1. 标题
2. Task ID
3. 项目名：novel-v1
4. 题材标签
5. 正文
6. 审核结果（PASS）
7. 生成日期

---

## 五、统一归档目录（强制）

**目录结构**：
```
novel-v1/
└── manuscripts/
    └── 2026-03-20/
        ├── novel-001-标题.docx
        └── novel-002-标题.docx
```

**归档规则**：
1. 按日期建文件夹
2. 每篇小说独立文件
3. 文件命名必须包含：Task ID + 标题
4. 不允许散落不同目录
5. 不允许只存在 markdown 无 docx

---

## 六、文件命名规范

**格式**：`{TaskID}-{ShortTitle}.docx`

**示例**：
- novel-001-婚约到期后.docx
- novel-002-替身新娘反杀记.docx

**要求**：Task ID 唯一，标题可简化但必须可识别

---

## 七、TASK-POOL 状态升级规则

小说任务状态必须细化为：

| 状态 | 说明 |
|------|------|
| 待执行 | 等待执行 |
| 执行中 | 写作中 |
| 待审核 | writer 已完成，等待 review |
| 待导出 | review 已 PASS，等待生成 docx |
| 已归档 | docx 已落地到统一目录 |
| 已完成 | 归档完成 + 日报已核对 |

---

## 八、导出失败处理机制

如果出现：
- 正文完成但未导出 docx
- docx 导出失败
- 文件未落到统一目录
- 文件命名不符合规范

则标记为：**EXPORT BLOCKED**，并记录原因。

---

## 九、Daily Report 核对机制（强制）

CEO 在 Daily Operating Report 中，针对 novel-v1 必须单独汇报：

1. **今日目标**：2 篇
2. **今日实际**：
   - 生成任务数
   - 完成正文数
   - PASS 数
   - 成功导出 docx 数
   - 成功归档数
3. **必须列出文件路径**：
   - novel-v1/manuscripts/2026-03-20/novel-001-xxx.docx
4. **如果没有 docx 文件落地**：今日产出 = 0

**核心原则**：
- 有任务卡 ≠ 有产出
- 有正文 ≠ 有归档
- **有归档路径 + 文件存在 = 才算完成**

---

## 十、遗漏防呆机制

CEO 每天结束前必须检查：
1. 今日 novel-v1 是否已触发
2. 今日 2 个任务是否都已进入 TASK-POOL
3. 是否都已进入 writer
4. 是否都已 review
5. 是否都已导出 docx
6. 是否都已归档
7. 日报是否写明文件路径

如任一项缺失，必须在当日标记异常，不得留到第二天模糊带过。

---

## 十一、系统禁止项

**禁止**：
1. 只生成 Task Card 不推进写作
2. 只完成写作不审核
3. 审核通过但不导出 docx
4. 导出 docx 但不归档到统一目录
5. 日报中将"历史文件"冒充"今日产出"
6. 用"今天忘记启动"作为常态解释

---

## 十二、成功标准

novel-v1 当日生产达标必须同时满足：
1. ✅ 生成 2 个小说任务
2. ✅ 2 篇都完成正文
3. ✅ 2 篇都通过 review
4. ✅ 2 篇都导出为独立 .docx
5. ✅ 2 篇都归档到统一目录
6. ✅ Daily Report 写明文件路径并核对无误

**否则**：今日 novel-v1 生产视为**未达标**

---

## 十三、第一阶段运行要求

先连续执行 3 天，观察：
1. 是否能自动启动
2. 是否能稳定完成 2 篇
3. 是否能稳定导出 docx
4. 是否能稳定归档
5. 日报是否真实反映产出

3 天后再做复盘，不要先扩复杂系统。

---

## 十四、核心原则总结

在 novel-v1 中：

- 自动生成任务 ≠ 自动完成生产
- 正文写完 ≠ 真正交付

**真正完成的定义是**：
> 任务创建 → 写作完成 → 审核通过 → docx 导出 → 文件归档 → 日报核对

**只有全部成立，才算真正完成。**

---

## Daily Production Rule（novel-v1）

### 1. 每日启动

- CEO 主动生成当日任务列表：novel-1, novel-2
- 不等待逐条任务分配

### 2. 任务生成流程

```
CEO
↓
调用 lead-novel
↓
生成 2 个 Story Task Card
↓
CEO 统一接收
```

### 3. 执行流程（每个任务）

```
lead-novel
↓
CEO 调度 story-editor
↓
CEO 调度 writer
↓
CEO 调度 review-editor
↓
结果回 lead-novel
```

### 4. 执行方式

- 可以顺序执行或并行执行
- **必须保证**：当日 2 篇任务全部进入执行流程
- **不允许**：完成 1 篇后等待下一次指令

### 5. 收口机制

每日结束输出 Production Report：
- novel-1 状态（PASS / REVISION / BLOCKED）
- novel-2 状态（PASS / REVISION / BLOCKED）
- 选题摘要
- 是否完成（2/2、1/2、0/2）
- 问题记录

### 6. 异常处理

- 如果某任务 BLOCKED：不影响另一任务继续执行
- 记录 Issue Log
- 不停止当日生产

### 7. 核心原则

**任务批量驱动**，不是单任务触发

---

# Research Protocol（商业导向版 2026-03-20）

## 一、核心定位

**Research Agent = Opportunity Engine（机会引擎）**

职责不是研究，而是：
- 👉 发现可以快速验证并尝试收费的真实项目机会

## 二、核心目标（必须同时满足）

Research 输出必须服务于完整闭环：

```
发现机会 → 立项 → MVP → 测试收费
```

如果不能进入该闭环：
- 👉 不算有效 Research

## 三、研究优先级（强制执行）

### A. 用户真实抱怨（最高优先级）

**数据来源**：
- Reddit、Hacker News、Product Hunt 评论
- IndieHackers、Chrome 插件评论、SaaS 评论

**重点关键词**：
- too expensive / too complicated / hard to use
- missing feature / I wish it could
- manual / repetitive / takes too long

**目标**：👉 找"付费意愿明确"的问题

### B. 新能力扫描

**数据来源**：
- 新模型（OpenAI / Anthropic / Google 等）
- API / 新工具、GitHub trending

**必须回答**：
- 这个能力可以变成什么小工具？
- 谁会为它付费？
- 是否适合 7 天内做 MVP？

**禁止**：❌ 只做技术介绍

### C. 竞品与定价

**必须分析**：
- 竞品功能、定价、差评/抱怨、缺失功能

**目标**：👉 找切入点，而不是复述市场

## 四、输出格式（强制）

```
【Opportunity Card】

1. 机会名称
2. 目标用户
3. 用户最痛的点
4. 现有解决方案及问题
5. 为什么现在值得做
6. MVP 最小功能集合
7. 建议定价方式
8. 验证路径（7天内）
9. 风险与不做原因
10. 最终结论（做 / 不做 / 观察）
```

## 五、输出质量标准

**必须满足**：
1. 可执行（能立项）
2. 可收费（有付费可能）
3. 可快速验证（≤7天）

**禁止**：
- ❌ 泛趋势分析
- ❌ 空洞总结
- ❌ 技术炫技

## 六、与 CEO 的关系

Research → CEO

CEO 使用 Research 输出：
- 创建新项目（lead-*）
- 调整方向、分配资源

Research 不做决策。

## 七、与 Project Lead 的关系

Project Lead 可以：
- 请求选题、请求竞品分析、请求用户洞察

Research 输出：
- 👉 可直接转 Task 的信息

## 八、与 lead-novel 的边界

Research：
- 提供题材趋势、市场偏好

lead-novel：
- 决定选题、生成任务、管内容生产

**原则**：
- 👉 Research 提供"可能赚钱的方向"
- 👉 Lead 决定"做哪一个"

## 九、运行频率（第一阶段）

- CEO 每周触发 2–3 次 Opportunity Research
- Project Lead 按需请求

**避免**：❌ 高频低质量

## 十、核心原则

> **Research ≠ 信息**  
> **Research = 可转化为收入的机会**

---

# Daily Operating Report（每日运营报告 2026-03-20）

## 报告目标

> 不是汇报任务，而是帮助 Founder 做决策。

---

## 一、项目进展（Project Level）

按项目逐一汇报，每个项目必须包含：

1. 项目名称（如 hub-v1 / sticker-v1 / novel-v1）
2. 当前阶段（如：MVP开发 / 内容生产 / 验证中）
3. 今日完成任务（列出 Task ID）
4. 当前进度（如：3/5 tasks）
5. 状态判断：正常 / 风险 / 阻塞
6. 一句话总结：👉 这个项目现在在往哪里走

---

## 二、产出分区（强制）

### 【今日新增产出】
👉 Completed Date = today

列出今日完成的所有任务，必须满足：
- Task 存在于 TASK-POOL.md
- Completed Date = 汇报当日

### 【历史产出引用】
👉 仅用于说明，不计入今日

引用历史任务必须标注：
- 实际完成时间（如：完成于 3月19日）

---

## 三、Time Validation（强制）

在报告开头必须包含：

```
[Time Validation]
✔ All tasks match Completed Date
```

或

```
❌ Found mismatch → BLOCKED
```

---

## 四、TASK-POOL 状态总览（Task Level）

必须汇总：
- 待执行任务数
- 执行中任务数
- 待验收任务数
- 已完成任务数
- 已阻塞任务数

并列出所有 BLOCKED 任务：
```
- Task ID + 原因
```

---

## 三、关键风险（Risk）

必须明确：
- 当前系统最大的 1–3 个问题
- 哪些任务卡住
- 哪些项目可能失败

必须说明：👉 原因 + 影响范围

---

## 四、机会与研究（Research & Opportunities）

### 1️⃣ 今日新增机会（New Opportunities）
- Opportunity 名称
- 来源（Reddit / Hacker News / PH 等）
- 核心痛点（一句话）

### 2️⃣ 机会状态（Opportunity Status）
每个机会标记：新发现 / 分析中 / 可立项 / 已转项目 / 放弃

### 3️⃣ 可立项机会（Top Opportunities）
列出 1–3 个：👉 可以立即做 MVP 的机会

必须说明：
- 为什么可以 7 天内做出来
- 为什么可能收费

### 4️⃣ Research 结论
一句话总结：👉 当前最值得做的机会是什么

---

## 五、决策建议（Decision Support）

CEO 必须明确给出：
1. 明天最优先做的 1–3 件事
2. 哪个项目继续推进
3. 哪个项目需要暂停 / 调整
4. 是否需要创建新项目（基于 Research）

---

## 六、系统健康度（System Health）

必须检查：
- 是否存在未进入 TASK-POOL 的任务
- 是否存在状态未更新
- 是否存在执行异常（超时 / 失败）
- TASK-POOL 是否完整

如果有问题：👉 必须指出

---

## 七、每日关键结论（Top Signals）

必须输出三条：
- 🔥 今日最重要进展（Top 1）
- ⚠️ 最大风险（Top 1）
- 🎯 明日唯一优先事项（Top 1）

---

## 八、报告时间

每日固定时间输出（建议：21:00）

---

## 九、核心原则

1. 不做流水账
2. 不只讲任务，必须讲项目
3. 不只讲现状，必须给判断
4. 不只讲执行，必须讲机会
5. 所有信息必须服务于决策

---

## 十、最终目标

让 Founder 一眼看懂：
👉 今天做了什么 / 哪些项目在推进 / 哪里有问题 / 有哪些赚钱机会 / 明天该做什么

---

# Weekly Strategy Report（周战略报告 2026-03-20）

## 报告目标

> 不是汇报执行，而是帮助 Founder 做战略决策。

---

## 一、本周总览（Executive Summary）

必须用 3–5 行总结：
- 本周最重要进展
- 系统整体状态（健康 / 风险 / 不稳定）
- 是否有"明显有效的方向"

---

## 二、项目评估（Project Review）

对每个项目进行评估（hub-v1 / sticker-v1 / novel-v1 等），每个项目必须包含：

1. **本周完成情况**
   - 完成了哪些任务（Task ID）
   - 是否达到阶段目标

2. **当前阶段**
   - MVP / 验证 / 迭代 / 停滞

3. **关键指标**（如适用）
   - 内容产量、用户反馈、是否有付费尝试、转化/点击（如有）

4. **问题与瓶颈**
   - 卡在哪
   - 是结构问题还是执行问题

5. **项目结论**（必须给出）
   - 继续推进 / 调整方向 / 暂停 / 终止

---

## 三、机会评估（Opportunity Review）

基于 Research 输出，评估：

1. 本周发现的机会数量
2. 进入"可立项"的机会（列出）

每个机会必须说明：
- 是否值得做、为什么、是否已进入项目

3. **当前最强机会（Top 1）**
👉 哪个最有可能变现

---

## 四、资源分配建议（Resource Allocation）

CEO 必须提出：
- 下周资源应该集中在哪个项目
- 哪些项目降低优先级
- 是否需要新增项目（基于 Research）

---

## 五、系统问题与优化（System Issues）

必须指出：
- Task Protocol 是否稳定
- 是否有漏任务 / 状态混乱
- 是否存在执行瓶颈（如 tiger-coder 超时）

并提出：👉 具体优化建议

---

## 六、执行效率分析（Execution Efficiency）

必须分析：
- 本周完成任务数量
- BLOCKED 比例
- REVISION 比例

结论：👉 系统效率是提升还是下降

---

## 七、下周战略重点（Next Week Strategy）

必须明确：
1. 下周唯一核心目标（Top 1）
2. 需要重点推进的 1–2 个项目
3. 是否启动新项目
4. 是否停止某个项目

---

## 八、Kill / Scale 决策（最关键）

CEO 必须明确：
- 哪个项目应该放大（Scale）
- 哪个项目应该停止（Kill）

**不允许全部继续**。

---

## 九、核心判断（最重要一句）

CEO 必须给出一句话：

👉 "当前 AI Company Model 最接近赚钱的方向是：____"

---

## 十、报告频率

每周一次（建议周日）

---

## 十一、核心原则

1. 不做流水总结
2. 必须做选择（取舍）
3. 必须给判断（不是描述）
4. 必须服务商业结果（赚钱 / 验证）

---

## 十二、最终目标

让 Founder 一眼看懂：
👉 哪些项目值得继续 / 哪些应该砍掉 / 哪个方向最可能赚钱 / 下周资源怎么用

---

# Project Registry Protocol（项目注册协议 2026-03-20）

## 目标

让系统具备"项目级管理能力"，避免：
- 项目遗漏
- 项目无法追踪
- Daily / Weekly 报告不完整
- 项目与任务脱节

---

## 一、核心原则（最高优先级）

1. **未注册项目 = 不存在**
2. **未进入 TASK-POOL 的项目 = 不允许运行**
3. **Project Registry 是唯一项目源（Single Source of Truth）**

---

## 二、Project Registry 定义

Project Registry 是系统中的：
👉 项目索引层（Project Index Layer）

用于记录：
- 所有项目
- 项目状态
- 项目负责人
- 项目阶段

---

## 三、项目创建强制流程

任何新项目必须按以下流程创建：

1. **Step 1**：CEO 确认立项
2. **Step 2**：创建 Project ID
3. **Step 3**：创建 Project Lead（lead-*）
4. **Step 4**：创建首个 Task（Task ID = xxx-001）
5. **Step 5**：写入 TASK-POOL
6. **Step 6**：注册到 Project Registry

**否则**：
- ❌ 项目不允许运行
- ❌ 不允许进入 Daily Report

---

## 四、Project ID 规范

格式：`{project-name}-v{version}`

**示例**：
```
hub-v1
sticker-v1
novel-v1
motionclean-v1
```

**规则**：
1. 全局唯一
2. 小写 + 短名称
3. 不允许修改（版本升级用 v2）

---

## 五、Project Registry 字段（强制）

每个项目必须包含：
1. Project ID
2. Project Name
3. Project Lead（lead-*）
4. Status（状态）
5. Stage（阶段）
6. Created Date
7. Last Updated
8. Total Tasks
9. Completed Tasks

---

## 六、项目状态（Status）

必须使用标准状态：
- ACTIVE（运行中）
- PAUSED（暂停）
- BLOCKED（阻塞）
- COMPLETED（完成）
- KILLED（终止）

---

## 七、项目阶段（Stage）

用于标识项目进度：
- IDEA（想法）
- MVP（开发）
- TEST（测试）
- ITERATION（迭代）
- SCALE（放大）

---

## 八、自动关联规则（关键）

Project Registry 与 TASK-POOL 必须关联：

**规则**：
- 每个 Task 必须绑定 Project ID
- Project 的 Task 数量必须来自 TASK-POOL

**禁止**：
- ❌ 项目脱离 TASK-POOL 存在

---

## 九、Daily Report 强制依赖

Daily Report 中：
👉 项目列表必须来源于 Project Registry

**禁止**：
- ❌ 手动补项目
- ❌ 使用记忆

**流程**：Project Registry → Project List → Daily Report

---

## 十、Weekly Report 强制依赖

Weekly Strategy Report：
👉 必须基于 Project Registry 做评估

**必须覆盖**：
- 所有 ACTIVE 项目
- 所有 BLOCKED 项目

---

## 十一、项目扫描机制（强制）

CEO 在生成报告前必须执行：

```
[Project Scan]
```

**输出**：
- 当前所有项目列表
- 每个项目状态

---

## 十二、异常处理机制

如果发现："任务存在，但项目未注册"

**必须**：
1. 创建 Project ID
2. 注册 Project
3. 补录 TASK-POOL

**标记为**：PROJECT VIOLATION

---

## 十三、Kill / Scale 决策绑定

Project Registry 必须支持：
- 标记项目为 KILLED
- 标记项目为 SCALE

用于 Weekly 决策。

---

## 十四、核心升级意义

本协议将系统从：
> 任务系统（Task System）

升级为：
> 👉 项目系统（Project System）

---

## 十五、核心原则总结

在 AI Company Model 中：
- **任务是执行单位**
- **项目是决策单位**

Project Registry 是：
> 👉 决策层基础

---

# Project Registry（项目注册表）

| Project ID | Project Name | Project Lead | Status | Stage | Cycle | Target | Created | Last Updated | Total Tasks | Completed |
|------------|--------------|--------------|--------|-------|-------|--------|---------|--------------|-------------|-----------|
| hub-v1 | AI 独立站 | lead-hub | ACTIVE | MVP | - | - | 2026-03-16 | 2026-03-16 | 3 | 3 |
| sticker-v1 | 表情包工具 | lead-sticker | ACTIVE | MVP | - | - | 2026-03-16 | 2026-03-16 | 3 | 3 |
| novel-v1 | 小说编辑部 | lead-novel | ACTIVE | ITERATION | DAILY | 2 | 2026-03-19 | 2026-03-19 | 4 | 4 |
| motionclean-v1 | MotionClean | lead-motionclean | ACTIVE | MVP | - | - | 2026-03-20 | 2026-03-20 | 5 | 5 |
| gateway-lite-v1 | 模型网关 | tiger-coder | ACTIVE | MVP | - | - | 2026-03-30 | 2026-03-30 | 0 | 0 |
| control-center-v1 | 控制平面 | tiger-coder | ACTIVE | MVP | - | - | 2026-03-30 | 2026-03-30 | 0 | 0 |

---

# Time Protocol（时间维度强制标注 2026-03-20）

## 一、核心原则

所有任务与产出必须区分：
- **Created Date**（创建时间）
- **Completed Date**（完成时间）
- **Report Date**（汇报时间）

**禁止**：
- ❌ 使用模糊描述（如：今天完成）
- ❌ 未标注时间直接汇报

---

## 二、Daily Report 时间规则

"今日完成任务"必须满足：
👉 Completed Date = 今日

**否则**：
- ❌ 不允许归入"今日完成"

---

## 三、历史产出规则

如果引用历史任务，必须标注：
- 实际完成时间

**格式**：hub-003（完成于 3月19日）

---

## 四、Task Protocol 升级

每个 Task 必须新增字段：
- Created Date
- Started Date
- Completed Date

---

## 五、报告校验机制

CEO 在生成报告前必须检查：
👉 所有"今日完成任务"是否满足时间条件

**否则**：BLOCKED：时间不一致

---

# Production KPI & Export KPI System（生产与交付指标系统 2026-03-20）

## 目标

让系统自动判断：
- 是否有产出
- 是否达标
- 是否完成交付（docx）
- 问题出在哪里

---

## 一、KPI 适用范围

适用于所有定义了 Production Rule 的项目：
- novel-v1（每日2篇小说）
- content-v1（每日内容）
- research-agent（每周机会）

---

## 二、核心 KPI 维度

### 1️⃣ Production KPI（生产指标）
- **Target**：目标产量
- **Actual**：实际产量
- **公式**：Production Rate = Actual / Target

### 2️⃣ Completion KPI（完成率）
任务是否走完：Task Created → Writing → Review → Done

### 3️⃣ Export KPI（交付指标）
- 统计 docx 成功生成数量
- 成功归档数量
- **公式**：Export Rate = Exported / Target

### 4️⃣ Quality KPI（质量指标）
- Review PASS 数
- Revision 数
- BLOCKED 数

### 5️⃣ Stability KPI（稳定性）
连续天数：
- 连续达标天数
- 连续失败天数

---

## 三、状态判定规则（强制）

| 状态 | 条件 |
|------|------|
| 🟢 **HEALTHY** | Production Rate = 100% 且 Export Rate = 100% |
| 🟡 **WARNING** | Production ≥ 50% 但未达标 |
| 🔴 **FAILED** | Production = 0 或 未导出 docx |

---

## 四、自动原因分类（必须）

如果 FAILED，必须自动归因：

| 原因 | 说明 |
|------|------|
| NOT_TRIGGERED | 未触发生产 |
| EXECUTION_DELAY | 执行未完成 |
| REVIEW_BLOCKED | 审核未通过 |
| EXPORT_FAILED | 未导出 docx |
| SYSTEM_ERROR | 系统问题 |

---

## 五、Daily Report 强制输出

每个生产项目必须输出：

```
Project: novel-v1

Target: 2
Actual: X
Production Rate: X%

Exported: X
Export Rate: X%

Status: 🟢 / 🟡 / 🔴
Reason（如失败）: XXXX
```

---

## 六、导出验证（关键）

只有满足以下条件才算"完成"：
1. docx 文件存在
2. 路径正确
3. 命名符合规范

**否则**：Export KPI = 0

---

## 七、连续失败机制

如果连续 2 天 FAILED：
- CEO 必须在 Weekly Report 中标记为风险项目

---

## 八、核心原则

> 没有 docx = 没有产出  
> 没有归档 = 没有完成  
> 没有 KPI = 不可管理

---

# Autonomous Progression Mechanism（任务自动推进机制 2026-03-20）

## 目标

确保任务链路可以自动推进：
> Task A 完成 → 自动触发 Task B

**不允许**：
- 等 Founder 提醒
- 等外部查询才继续
- 停在中间节点

---

## 一、适用范围

适用于所有存在"任务链路"的项目：
- novel-v1：选题 → 大纲 → 写作 → 审核 → 导出
- motionclean：模块1 → 模块2 → 模块3
- hub-v1：页面1 → 页面2 → 页面3

---

## 二、核心机制

每一个 Task 在完成后，必须执行：
> **Next Step Detection（下一步检测）**

**执行逻辑**：
1. 当前 Task 标记为 DONE
2. 自动查询 TASK-POOL：是否存在该项目的下一个任务？
3. 若存在 → 立即触发执行（无需等待指令）
4. 若不存在 → 检查是否需要创建新任务

---

## 三、链路类型识别（关键）

### 1️⃣ Linear Chain（线性链路）
mc-1 → mc-2 → mc-3 → mc-4

**规则**：完成 mc-3 后 → 自动触发 mc-4

### 2️⃣ Pipeline Chain（流水线）
novel-v1：选题 → 大纲 → 写作 → 审核 → 导出

**规则**：
- writer 完成后 → 自动进入 review
- review PASS 后 → 自动进入 export

### 3️⃣ Batch Production（批量生产）
每日 2 篇小说：novel-001, novel-002

**规则**：完成一个任务不影响另一个任务推进

---

## 四、自动推进规则（强制）

每个 Task 完成后，必须执行：
1. 更新 TASK-POOL 状态 → DONE
2. 执行 Next Step Detection
3. 如果存在下一个任务 → 自动 dispatch 给对应 Agent
4. 如果不存在 → 判断：
   - 属于生产链路 → 继续生成
   - 属于终点 → 标记完成

---

## 五、禁止行为

- ❌ Task 完成后停住
- ❌ 等待人工触发下一步
- ❌ 仅汇报，不推进
- ❌ "等待指示"作为默认行为

---

## 六、异常处理机制

如果推进失败，必须标记原因：

| 原因 | 说明 |
|------|------|
| NEXT_TASK_NOT_FOUND | 没有下一个任务 |
| AGENT_NOT_AVAILABLE | 执行 Agent 不存在 |
| CONTEXT_MISSING | 上下文缺失 |
| SYSTEM_ERROR | 系统异常 |

并记录在 TASK-POOL。

---

## 七、自检机制（每次必做）

每次任务完成后，必须自检：
1. 我这个任务是不是链路中的一环？
2. 后面还有没有任务？
3. 我有没有触发它？

**如果答案是"有但没触发"**：立即补执行（不允许等待）

---

## 八、CEO 强制职责升级

CEO Agent 新增职责：
> **Flow Controller（流程控制器）**

**职责**：
- 确保所有链路不中断
- 检查是否有任务卡住
- 主动推进，而不是被动响应

---

## 九、成功标准

一个项目链路被认为"健康运行"，必须满足：
- 任一任务完成后 ≤5秒 内触发下一步
- 无人工干预即可完成完整链路
- 无"等待提醒"行为

---

## 十、核心原则

> 完成任务 ≠ 完成工作  
> 推进链路 = 才算完成

系统必须具备：
> **自驱动执行能力（Self-Driving Execution）**

---

# Bottleneck Detection System（瓶颈识别系统 2026-03-20）

## 目标

让系统自动发现：
- 哪个任务阶段最慢
- 哪个 Agent 最容易卡住
- 哪个项目最不稳定
- 哪个环节在拖慢产出和变现

---

## 一、系统定位

**Bottleneck Detection System = 流程诊断层**

**作用**：
1. 自动识别项目推进中的瓶颈
2. 自动指出最常见失败环节
3. 为 CEO 提供优化建议
4. 为 Founder 提供资源分配依据

---

## 二、瓶颈识别对象

### 1️⃣ Agent Bottleneck
- 哪个 Agent 最常 timeout
- 哪个 Agent 最常 BLOCKED
- 哪个 Agent 最常需要 revision

### 2️⃣ Task Stage Bottleneck
- 哪个阶段最慢
- 哪个阶段最容易失败
- 例如：planning / execution / review / export

### 3️⃣ Project Bottleneck
- 哪个项目推进最慢
- 哪个项目失败率最高
- 哪个项目最不稳定

### 4️⃣ Output Bottleneck
- 哪个环节导致"有任务但无交付"
- 哪个环节导致"有正文但无文件"
- 哪个环节导致"有文件但无通过审核"

---

## 三、瓶颈判断依据（强制）

必须基于以下数据判断瓶颈：
1. Task 执行时长
2. Task BLOCKED 次数
3. Revision 次数
4. Export Failure 次数
5. 未达标周期（Daily / Weekly / Monthly）
6. Agent timeout / failed 次数

**禁止**：
- ❌ 用主观感觉判断瓶颈
- ❌ 只凭一次异常就下结论

---

## 四、Bottleneck Metrics（指标）

每个项目 / Agent / 阶段必须统计：
1. **Avg Duration**（平均耗时）
2. **Blocked Count**（阻塞次数）
3. **Revision Count**（返工次数）
4. **Failure Count**（失败次数）
5. **Completion Rate**（完成率）
6. **Export Rate**（导出率）

---

## 五、瓶颈识别规则

满足以下任一条件，自动标记为瓶颈：
1. 某 Agent 连续 2 次 timeout
2. 某阶段 Avg Duration 显著高于其他阶段
3. 某项目连续 2 个周期 FAILED
4. 某任务类型 Revision Rate > 50%
5. 某项目 Export Rate < 50%

---

## 六、瓶颈分类输出

**标准格式**：

```
[Bottleneck Report]

1. Bottleneck Type:
2. Scope（Agent / Project / Stage）:
3. Evidence（依据）:
4. Impact（影响）:
5. Suggested Fix（建议修复）:
```

**示例**：
```
Bottleneck Type: Stage Bottleneck
Scope: review-editor
Evidence: 过去7天review平均耗时最高，revision次数最多
Impact: novel-v1无法稳定日产2篇
Suggested Fix: 降低review粒度/简化审核标准/优先处理结构问题
```

---

## 七、Daily Report 规则

Daily Report 中新增：
> **【Bottleneck Watch】**

包含：
- 今日最大瓶颈（Top 1）
- 影响项目
- 是否需要立即处理

---

## 八、Weekly Report 规则

Weekly Strategy Report 中新增：
> **【Weekly Bottleneck Summary】**

必须包含：
1. 本周最主要瓶颈
2. 最常失败环节
3. 最低效率项目
4. 下一周优先修复项（Top 1）

---

## 九、CEO 新职责

CEO Agent 新增职责：
> **Bottleneck Manager**

**职责**：
1. 每日扫描瓶颈
2. 每周总结瓶颈
3. 给出修复优先级
4. 决定是：修 / 绕 / 降级 / 终止

---

## 十、Founder 决策支持

Founder 应根据瓶颈报告判断：
- 是 Agent 问题
- 是协议问题
- 是流程问题
- 是项目本身不值得做

---

## 十一、禁止行为

- ❌ 发现瓶颈但不记录
- ❌ 只抱怨，不归因
- ❌ 每次都靠 Founder 问才意识到卡住

---

## 十二、核心原则

> 低产出不是问题本身  
> 找不到瓶颈，才是最大问题

系统必须做到：
> 发现问题 → 定位瓶颈 → 给出修复建议

---

## 十三、最终目标

让系统具备：
- 自我诊断
- 自我优化建议
- 持续提升产能与效率

---

# Agent Architecture Proposal Protocol（项目建制提案机制 2026-03-20）

## 目标

确保新项目创建经过审批流程，避免盲目扩张 Agent 组织。

---

## 一、触发条件

当 Founder 提出新的项目需求时：
1. CEO **不要**直接创建 Agent
2. CEO 必须先输出《Agent Architecture Proposal》
3. 未经 Founder 审批，**不允许**正式创建新 Agent

---

## 二、Proposal 判断清单

CEO 必须先判断：
1. 这是**新项目**，还是**现有项目子任务**？
2. 是否需要新建 Project Lead（lead-*）？
3. 是否需要新增执行层 Agent，还是**复用**现有执行层？

---

## 三、Agent Architecture Proposal 格式

必须包含以下 10 项：

```
1. Project Name:
2. Project Type:
3. Goal:
4. Why New Project:
5. Proposed Project Lead（新建 / 复用）:
6. Proposed Execution Agents（新建 / 复用）:
7. Agent Responsibilities:
   - 职责：
   - 边界：
   - 不负责什么：
8. Runtime Flow:
9. Production / Operating Rhythm:
10. Approval Request:
    [ ] Approve
    [ ] Revise
    [ ] Reject
```

---

## 四、审批流程

```
Founder 提出需求
       ↓
CEO 输出 Proposal
       ↓
Founder 审批（Approve / Revise / Reject）
       ↓
若 Approve → CEO 输出 Approved Deployment Plan
       ↓
执行建制
```

---

## 五、Approved Deployment Plan 格式

审批通过后，CEO 必须输出：

```
1. 要创建的 Agent:
2. 要复用的 Agent:
3. Project ID:
4. 写入 Project Registry 的内容:
5. 首批 Task Card:
6. Runtime 调度路径:
```

---

## 六、默认原则

- **新项目** → 优先新建 lead-*
- **执行层** → 优先复用
- CEO → 只负责提案，不负责越权扩组织
- Founder → 保留最终审批权

---

## 七、禁止行为

- ❌ 未经审批直接创建 Agent
- ❌ 未经审批写入 Project Registry
- ❌ CEO 自行判断"不需要 Lead"
- ❌ 用"复用"绕过审批

---

## 八、核心原则

> 新项目 = 提案 + 审批 + 建制  
> 不审批 = 不建制

---

# 📄 Agent Architecture Proposal（组织架构提案模板）

> 用于：CEO 接到需求后输出（必须先出这个，不能直接建 Agent）

---

## 【1. Project Overview】

**Project Name**:（项目名称，例如：motionclean-v1）

**Project Type**:（tool / content / research / ops）

**Goal**:（一句话目标：解决什么问题 / 验证什么）

**Example**: Build an AI tool to automatically clean motion capture data and fix finger animation issues.

---

## 【2. Why This Project】

**Why create a new project instead of using an existing one**:

- 是否独立目标？
- 是否需要独立节奏？
- 是否与现有项目边界不同？

**Conclusion**:（New Project / Merge into existing）

---

## 【3. Project Lead Design】

**Proposed Lead Agent**:

- **Name**: lead-xxxx
- **Type**: Project Lead
- **Decision**: [New / Reuse]

**Responsibilities**:
- 负责项目目标拆解
- 生成 Task Cards
- 控制范围（避免 scope creep）
- 负责 Review & Acceptance
- 汇报项目进展

**NOT Responsible**:
- 不直接写代码
- 不做执行层工作

---

## 【4. Execution Layer Design】

**Execution Agents**:

1. **Agent Name**: tiger-coder（示例）
   - **Decision**: [Reuse / New]
   - **Responsibilities**: 代码开发、技术实现、输出 deliverables

2. **Agent Name**:（如需要新增）
   - **Responsibilities**:（写清楚）

**Rule**: 优先复用现有执行层，只有不适配才新增

---

## 【5. Agent Interaction Flow】

**Runtime Flow**:

```
Founder
→ CEO (main)
→ Project Lead (lead-xxx)
→ CEO (runtime control)
→ Execution Agent (xxx)
```

**说明**:
- CEO 负责调度（sessions_spawn）
- Project Lead 不直接调用执行层（除非特殊设计）

---

## 【6. Task Flow Design】

**Task Flow**:

1. Lead 创建 Task Card
2. CEO 调度执行
3. Execution Agent 执行
4. Lead 做 Review
5. 完成 / Revision / Block

---

## 【7. Production / Operating Rhythm】

**是否需要周期机制**:

- **Daily**: 
- **Weekly**: 
- **Monthly**: 

**Example**: Daily: 2 tasks / Weekly: feature iteration

---

## 【8. Output & Deliverables】

**输出物**: 代码 / 页面 / 文档 / 文件（如 docx / json / etc）

**是否需要归档机制**: Yes / No

---

## 【9. Risks & Constraints】

**可能风险**:
- 技术难度
- Agent能力不足
- 执行链路不稳定

---

## 【10. Approval Request】

**Founder Decision Required**:

- [ ] Approve
- [ ] Revise
- [ ] Reject

**Optional Notes**:（Founder 可补充要求）

---

## 状态定义

| 状态 | 说明 |
|------|------|
| 待执行 | 任务已创建，等待分配 |
| 执行中 | 任务已分配给 tiger-coder，正在执行 |
| 已完成 | 任务成功完成，产出已交付 |
| 已阻塞 | 任务遇到阻塞，需要人工介入 |

---

# 📄 Approved Deployment Plan（部署执行方案模板）

> 用于：Founder 批准后，CEO 自动生成并执行

---

## 【1. Project Registration】

**Project ID**:（如：motionclean-v1）

**Project Name**:（项目名称）

**Status**: ACTIVE

**Stage**: MVP

---

## 【2. Agent Creation / Reuse】

**Project Lead**:

- **Name**: lead-xxxx
- **Action**: [Create / Reuse]
- **Workspace**: ~/.openclaw/workspace-lead-xxxx

**Execution Agents**:

1. **tiger-coder**
   - **Action**: Reuse

2. **xxx-agent**（如有）
   - **Action**: Create / Reuse

---

## 【3. openclaw.json 更新】

**需要更新**:

1. 注册 lead agent
2. 配置 subagents（如需要）
3. 更新 main allowAgents

**新增**:
- lead-xxxx

**规则**:
- CEO 只允许调用 Project Lead
- 执行层通过 runtime 调度

---

## 【4. Project Registry 写入】

**新增项目**:
- Project ID
- Lead Agent
- Status
- Stage
- Created Date

---

## 【5. Initial Task Setup】

**创建首批任务**:

**Task 1**:
- **ID**: xxx-001
- **描述**:
- **优先级**:

**Task 2**:
- **ID**: xxx-002
- ...

写入 TASK-POOL

---

## 【6. Runtime Execution Plan】

**执行链路**:

```
CEO → lead-xxxx → CEO → execution agent
```

**说明**:
- CEO 持有 sessions_spawn
- Lead 只负责任务拆解和验收

---

## 【7. Production Rule（如有）】

**Cycle Type**: DAILY / WEEKLY / NONE

**Target**:（如：每日2个任务）

---

## 【8. Validation Checklist】

**发布前必须确认**:

- [ ] Project 已注册
- [ ] Lead Agent 可调用
- [ ] Execution Agent 可用
- [ ] TASK-POOL 已写入
- [ ] 链路可运行

---

## 【9. Go-Live】

**状态**: READY → RUNNING

**CEO 开始调度执行**

---

# Auto Project Scoring（项目评分系统 2026-03-20）

## 目标

让 CEO 自动判断：
- 做不做
- 优先级
- 要不要建项目

---

## 🧩 1. 评分维度（固定 5 项）

| 维度 | 说明 |
|------|------|
| 1. Pain Level | 痛点强度 |
| 2. Monetization | 变现能力 |
| 3. MVP Feasibility | 实现难度 |
| 4. Speed | 验证速度 |
| 5. Competition | 竞争程度 |

---

## 🧠 2. 每项评分规则（1–5 分）

### 1️⃣ Pain Level（痛点强度）

| 分数 | 说明 |
|------|------|
| 1 | 可有可无 |
| 3 | 有点烦 |
| 5 | 强烈抱怨（必须解决） |

### 2️⃣ Monetization（变现能力）

| 分数 | 说明 |
|------|------|
| 1 | 难收费 |
| 3 | 可间接变现 |
| 5 | 用户愿意直接付钱 |

### 3️⃣ MVP Feasibility（实现难度）

| 分数 | 说明 |
|------|------|
| 1 | 复杂系统 |
| 3 | 中等 |
| 5 | 几天能做出来 |

### 4️⃣ Speed（验证速度）

| 分数 | 说明 |
|------|------|
| 1 | >1个月 |
| 3 | 1-2周 |
| 5 | 7天内验证 |

### 5️⃣ Competition（竞争程度）

| 分数 | 说明 |
|------|------|
| 1 | 红海 |
| 3 | 中等 |
| 5 | 空白/差评多 |

---

## 🔥 3. 最终评分公式

```
Total Score = Pain + Monetization + MVP + Speed + Competition
```

**满分**：25 分

---

## 🚦 4. 决策规则

| 分数 | 决策 |
|------|------|
| 21–25 | 立即立项（HIGH PRIORITY） |
| 16–20 | 可做（MEDIUM） |
| 10–15 | 观察（LOW） |
| <10 | 不做（REJECT） |

---

## 🧩 5. CEO 输出格式

```
[Project Scoring]

Pain Level: X
Monetization: X
MVP Feasibility: X
Speed: X
Competition: X

Total Score: XX

Decision: APPROVE / MEDIUM / LOW / REJECT
```

---

# Agent Library（Agent 模板库 2026-03-20）

## 目标

让 CEO 不用每次重新设计 Agent，而是：
> 选模板 → 微调 → 生成 Agent

---

## 1. Agent Library 总结构

1. **Project Lead Templates**（项目负责人模板）
2. **Execution Agent Templates**（执行层模板）
3. **Shared Capability Templates**（共享能力模板）
4. **Control Layer Templates**（控制层模板）

---

## 2. 通用 Agent 模板结构

所有 Agent 必须遵循以下结构：

| 字段 | 说明 |
|------|------|
| **Agent Name** | Agent 名称 |
| **Agent Type** | Project Lead / Execution / Shared / Control |
| **Core Responsibility** | 核心职责（3-5 条，必须具体） |
| **Inputs** | 从谁接收什么 |
| **Outputs** | 交付什么 |
| **Boundaries** | 明确不能做什么 |
| **Interaction** | 调用关系 |
| **Failure Handling** | 失败怎么处理 |
| **KPI** | 怎么衡量好坏 |

---

## 3. 核心模板（可直接使用）

### A. Project Lead 模板

```
Agent Name: lead-<project>
Type: Project Lead

Core Responsibility:
1. 拆解项目目标为 Task Cards
2. 控制任务范围（避免 scope creep）
3. 验收执行结果（Review）
4. 管理项目节奏（Daily / Weekly）
5. 记录 Issue Log

Inputs:
- CEO 分配的项目目标
- Research 输出（如有）

Outputs:
- Task Cards
- Review Results
- Issue Logs

Boundaries:
- ❌ 不写代码
- ❌ 不直接执行任务
- ❌ 不绕过 CEO 调用执行层

Interaction:
CEO → lead → CEO → execution agent

Failure Handling:
- 任务失败 → 标记 BLOCKED
- 需要修改 → REVISION
- 连续失败 → 上报 CEO

KPI:
- Task 完成率
- Review 通过率
- 项目推进速度
```

### B. Execution Agent 模板（通用）

```
Agent Name: <exec-agent>
Type: Execution Agent

Core Responsibility:
1. 执行 Task Card
2. 输出具体交付物（代码/文档/文件）
3. 保证结果可运行/可用

Inputs:
- Task Card（必须完整）

Outputs:
- Deliverable（代码/文件等）

Boundaries:
- ❌ 不定义任务
- ❌ 不做项目决策
- ❌ 不修改目标

Interaction:
CEO → execution agent

Failure Handling:
- 无法执行 → 返回原因
- 超时 → 标记 TIMEOUT

KPI:
- 执行成功率
- 平均耗时
- 超时率
```

### C. Research Agent 模板

```
Agent Name: research-agent
Type: Shared Capability

Core Responsibility:
1. 发现真实用户需求（抱怨/痛点）
2. 扫描新能力（模型/API）
3. 识别可快速变现机会

Inputs:
- CEO 请求
- 外部数据源

Outputs:
- Opportunity Card

Boundaries:
- ❌ 不做产品开发
- ❌ 不输出纯趋势分析

Output Format:
1. 机会名称
2. 目标用户
3. 核心痛点
4. 现有方案问题
5. MVP方案
6. 定价建议
7. 7天验证路径
8. 结论（做/不做）

KPI:
- 可执行机会数量
- 转化为项目的比例
```

### D. Novel 编辑部模板

```
Agents:
- lead-novel
- story-editor
- writer
- review-editor

核心结构：
lead-novel → story-editor → writer → review-editor

职责拆分：
- lead-novel：选题 + 控节奏
- story-editor：结构设计
- writer：正文输出
- review-editor：审核 + 风险控制
```

---

## Round 1 任务（2026-03-16）✅ 完成

### hub-v1（独立站项目）

| 任务ID | 描述 | 状态 | 执行时间 | 产出 |
|--------|------|------|----------|------|
| hub-1 | 优化 index.html 页面结构 | ✅ 已完成 | 35.7s | index.html |
| hub-2 | 创建 about.html 页面 | ✅ 已完成 | 24.0s | about.html |
| hub-3 | 为首页增加 About 页面链接 | ✅ 已完成 | 16.7s | index.html (updated) |

### sticker-v1（表情包项目）

| 任务ID | 描述 | 状态 | 执行时间 | 产出 |
|--------|------|------|----------|------|
| sticker-1 | 新增"社交分享"按钮 | ✅ 已完成 | 54.2s | page.tsx |
| sticker-2 | 增加"表情包预览区域" | ✅ 已完成 | 80.2s | page.tsx |
| sticker-3 | 增加页面 footer | ✅ 已完成 | 31.4s | page.tsx |

---

## 实验记录

### Timeout 配置
- **当前 timeout**：180s（3分钟）
- **配置位置**：`openclaw.json` → `agents.defaults.subagents.runTimeoutSeconds`

### 状态流转记录

| 时间 | 任务ID | 从状态 | 到状态 | 备注 |
|------|--------|--------|--------|------|
| 09:39 | hub-1 | - | 拆解中 | 派发给 lead-hub |
| 09:39 | hub-2 | - | 待执行 | - |
| 09:39 | hub-3 | - | 待执行 | - |
| 09:39 | sticker-1 | - | 拆解中 | 派发给 lead-sticker |
| 09:39 | sticker-2 | - | 待执行 | - |
| 09:39 | sticker-3 | - | 待执行 | - |
| 09:40 | hub-1 | 拆解中 | 执行中 | 派发给 tiger-coder |
| 09:40 | sticker-1 | 拆解中 | 执行中 | 派发给 tiger-coder |
| 09:40 | sticker-2 | 待执行 | 执行中 | 派发给 tiger-coder |
| 09:40 | sticker-3 | 待执行 | 执行中 | 派发给 tiger-coder |
| 09:42 | hub-1 | 执行中 | 已完成 | 35.7s |
| 09:43 | hub-2 | 待执行 | 执行中 | 派发给 tiger-coder |
| 09:44 | sticker-3 | 执行中 | 已完成 | 31.4s |
| 09:44 | sticker-1 | 执行中 | 已完成 | 54.2s |
| 09:45 | sticker-2 | 执行中 | 已完成 | 80.2s |
| 09:45 | hub-2 | 执行中 | 已完成 | 24.0s |
| 09:45 | hub-3 | 待执行 | 执行中 | 派发给 tiger-coder |
| 09:45 | hub-3 | 执行中 | 已完成 | 16.7s |

---

## 待办

- [x] 等待 lead-hub 完成任务拆解
- [x] 等待 lead-sticker 完成任务拆解
- [x] 调用 tiger-coder 执行任务 #1
- [x] 调用 tiger-coder 执行任务 #2
- [x] 调用 tiger-coder 执行任务 #3
- [x] 调用 tiger-coder 执行任务 #4
- [x] 调用 tiger-coder 执行任务 #5
- [x] 调用 tiger-coder 执行任务 #6
- [x] Round 1 总结
- [ ] 启动 novel-v1 每日生产

---

## Round 2 任务（2026-03-19）- 小说编辑部

### 2026-03-30 新增任务

|Task ID|描述|状态|执行时间|产出|
|--------|------|------|----------|------|
| novel-21 | 短篇 #21：隐婚甜约 - 现代都市甜宠契约婚姻，先婚后爱 | ✅ 已完成 | 2026-03-30 06:09 | 5000字, PASS, docx |
| novel-22 | 短篇 #22：重生后我成了boss的心尖宠 - 重生职场爽文 | ✅ 已完成 | 2026-03-30 06:09 | 5000字, PASS, docx |

### 2026-03-29 新增任务

|Task ID|描述|状态|执行时间|产出|
|--------|------|------|----------|------|
| novel-19 | 短篇 #19：豪门继女 - 豪门继女为拯救家族公司，被迫嫁给名义上的"养兄"，婚后发现只是商业交易棋子 | ✅ 已完成 | 2026-03-29 | 10000字, PASS, docx |
| novel-20 | 短篇 #20：职场逆袭 - 被男友闺蜜背叛后，职场小白成为集团空降COO助理，一路逆袭打脸 | ✅ 已完成 | 2026-03-29 | 7500字, PASS, docx |

|Task ID|描述|状态|执行时间|产出|
|--------|------|------|----------|------|
| novel-17 | 短篇 #17：闪婚甜宠 - 财阀继承人与普通女孩契约结婚，先婚后爱，从互相试探到真心交付 | ✅ 已完成 | 2026-03-28 | 11000字, PASS, docx |
| novel-18 | 短篇 #18：穿书女配 - 科研女博士穿成校园甜文里的恶毒女配，避开原剧情后被病娇男主反向追求 | ✅ 已完成 | 2026-03-28 | 8000字, PASS, docx |

### 2026-03-27 新增任务

|Task ID|描述|状态|执行时间|产出|
|--------|------|------|----------|------|
| novel-15 | 短篇 #15：职场逆袭 - 底层员工苏晚发现领导泄露公司机密，在24小时内收集证据自保反击，实现价值觉醒 | 待执行 | - | - |
| novel-16 | 短篇 #16：年代文（1992） - 少女林小满在父亲失业、家庭重病困境中，在选秀梦想与家庭责任之间做出抉择 | 待执行 | - | - |

### 2026-03-26 新增任务

|Task ID|描述|状态|执行时间|产出|
|--------|------|------|----------|------|
| novel-11 | 短篇 #11：AI生成题材A (补偿任务) | 待执行 | - | - |
| novel-12 | 短篇 #12：AI生成题材B (补偿任务) | 待执行 | - | - |

### 2026-03-24 新增任务

|Task ID|描述|状态|执行时间|产出|
|--------|------|------|----------|------|
| novel-9 | 短篇 #9：AI生成题材A (补偿任务) | 已完成 | 2026-03-25 | 重生千金 |
| novel-10 | 短篇 #10：AI生成题材B (补偿任务) | 已完成 | 2026-03-25 | 甜妻在上 |
| test-1 | [dispatch验证] 测试任务：写一段50字的小故事 | ✅ 已完成 | - | 小故事：猫和鱼 |
| test-2 | [完整链路验证] novel-v1：生成一篇2000字短篇小说 → review → export docx | ✅ 已完成 | 2026-03-25 | 1851字小说《甜蜜翻墙》 |
| e2e-1 | [E2E验证] 小说编辑部正式链路测试 | 待执行 | - | - |

### novel-v1（每日2篇短篇）

| 任务ID | 描述 | 状态 | 执行时间 | 产出 |
|--------|------|------|----------|------|
| novel-1 | 短篇 #1：隐婚三年的全职太太 | ✅ 已完成 (2026-03-19) | - | 15000字 PASS |
| novel-2 | 短篇 #2：死亡预言 | ✅ 已完成 (2026-03-19) | - | 15000字 PASS |
| novel-3 | 短篇 #3：《假面夫妻》 | ✅ 已完成 (2026-03-21) | 35s | 12,813字 |
| novel-4 | 短篇 #4：《继承者们》 | ✅ 已完成 (2026-03-21) | 1m | - |
| novel-5 | 短篇 #5：替身新娘 | ✅ 已完成 (2026-03-22) | 2m | PASS, docx |
| novel-6 | 短篇 #6：职场重生 | ✅ 已完成 (2026-03-22) | 2m | PASS, docx |
| novel-7 | 短篇 #7：豪门弃妇逆袭 | ✅ 已完成 (2026-03-23) | 2m30s | PASS, docx |
| novel-8 | 短篇 #8：互换人生 | ✅ 已完成 (2026-03-23) | 2m30s | PASS, docx |

---

### 2026-03-19 质量检查记录

**novel-2 相似性检查（2026-03-19 09:16）**

对比作品：《暗夜通灵师：我的眼睛能看到死期》（番茄小说）

| 维度 | 对比结果 | 风险等级 |
|------|----------|----------|
| 核心设定 | 同为"看到死亡时间"概念 | ⚠️ 中 |
| 主角身份 | 不同（高中生 vs 心理咨询师） | ✅ |
| 能力者 | 不同（主人公主观 vs 第三方患者） | ✅ |
| 关键反转 | 我们有"心死"反转 | ✅ |
| 具体情节 | 无桥段复制 | ✅ |

**结论**：类型设定相似（非具体抄袭），属常见悬疑套路
**后续建议**：避免重复"死亡预言"类题材

---

### Production Report（2026-03-19）

**目标**: 2 篇短篇小说

| 篇目 | 选题 | 大纲 | 正文 | 审核 | 状态 |
|------|------|------|------|------|------|
| #1 | ✅ 隐婚三年的全职太太 | ✅ 5章结构 | ✅ 15000字 | ✅ PASS | ✅ 完成 |
| #2 | ✅ 死亡预言 | ✅ 12章结构 | ✅ 15000字 | ✅ PASS | ✅ 完成 |

**关键问题**: ⚠️ novel-2 与热门作品《暗夜通灵师》核心设定相似（中风险），已记录

---

# Failure Protocol（失败处理与自恢复机制 2026-03-22）

## 目标

让系统具备：
- 👉 自检测（Detect）
- 👉 自恢复（Recover）
- 👉 自补偿（Compensate）
- 👉 自降级（Degrade）

---

## 一、失败类型定义（必须统一）

系统必须识别以下失败类型：

| 类型 | 英文 | 说明 |
|------|------|------|
| 1️⃣ | TRIGGER FAILURE | Heartbeat 未执行 / 定时触发失效 |
| 2️⃣ | PRODUCTION FAILURE | 未生成任务 / 未达到 Target |
| 3️⃣ | FLOW FAILURE | 任务链路中断（未自动推进） |
| 4️⃣ | EXECUTION FAILURE | Agent 超时 / 执行失败 |
| 5️⃣ | EXPORT FAILURE | 无 docx / 无文件交付 |
| 6️⃣ | DATA FAILURE | TASK-POOL 状态错误 / Report 与实际不一致 |

---

## 二、失败检测机制（自动）

系统在 Daily Report 生成前必须自动检测：

1. Heartbeat 是否执行
2. 是否有项目未触发任务
3. 是否存在卡住的任务（未推进）
4. 是否存在未导出的完成任务
5. KPI 是否异常（Production / Export）

**如发现**：👉 必须标记 FAILED（不能忽略）

---

## 三、自恢复机制（Recovery）

当检测到失败时，必须立即执行：

### 1️⃣ Heartbeat 未执行

→ 立即补执行（Compensate Run）

并记录：
- Missed Cycle: Yes
- Recovery: Executed

### 2️⃣ 任务未生成

→ 立即补生成任务  
→ 写入 TASK-POOL  

### 3️⃣ 链路中断

→ 自动执行 Next Step Detection  
→ 推进到下一 Agent  

### 4️⃣ 执行失败

→ 自动 Retry（最多1次）  
→ 再失败 → 标记 BLOCKED  

### 5️⃣ 未导出

→ 强制触发 export  
→ 未成功 → 标记 EXPORT FAILURE  

---

## 四、补偿机制（Compensation）

如果某周期任务未执行，下一次 Heartbeat 必须：

1. 检测缺失周期
2. 自动补任务
3. 标记为：**COMPENSATED TASK（补偿任务）**

**注意**：
- ❌ 补偿任务 ≠ 正常产出
- 必须单独标记

---

## 五、降级机制（Degradation）

如果连续失败：

| 连续失败天数 | 措施 |
|-------------|------|
| **2 天** | 标记项目：⚠️ AT RISK |
| **3 天** | 执行 Project Degradation：停止新增任务，仅允许修复任务，标记：🔴 DEGRADED |
| **5 天** | 建议：KILL PROJECT |

---

## 六、Daily Report 新增模块

```
[Failure & Recovery]

1. 今日失败类型：
   - TRIGGER FAILURE: Yes/No
   - PRODUCTION FAILURE: Yes/No
   - FLOW FAILURE: Yes/No
   - EXECUTION FAILURE: Yes/No
   - EXPORT FAILURE: Yes/No
   - DATA FAILURE: Yes/No

2. 是否执行 Recovery：X/Y
3. 是否执行 Compensation：X/Y
4. 是否触发 Degradation：None / AT RISK / DEGRADED
```

---

## 七、CEO 新职责

CEO Agent 新增角色：

👉 **Failure Manager**

职责：
1. 自动检测失败
2. 自动执行恢复
3. 记录失败原因
4. 决定是否降级

---

## 八、禁止行为

- ❌ 发现失败但不处理
- ❌ 用解释代替修复
- ❌ 等 Founder 提醒才恢复
- ❌ 把失败当"正常情况"

---

## 九、核心原则

> 失败不可避免  
> 不可恢复才是问题

系统必须做到：

**发现 → 修复 → 记录 → 优化**

---

## 十、最终目标

让系统具备：
- 👉 连续运行能力（Resilience）
- 👉 自恢复能力（Self-healing）
- 👉 抗中断能力（Fault tolerance）

---

# 附录：失败检测 Checklist

## Daily Report 生成前必检

```
[ ] Heartbeat 今日是否执行
[ ] ACTIVE 项目是否都有今日任务
[ ] 是否有任务卡在"执行中"超过 1 小时
[ ] 是否有任务"待验收"超过 24h 未审核
[ ] 是否有任务已完成但未导出 docx
[ ] Production Rate 是否达标
[ ] Export Rate 是否达标
```

如任何一项 Yes → 执行 Recovery
