# HEARTBEAT.md - 系统心跳执行逻辑

**版本**: 1.2
**用途**: 每日 09:00 自动调度（由 Cron 触发）

---

## Dispatch 标准模板（必须遵守！）

每次 dispatch subagent 必须包含：

### 1. cwd 配置
```python
sessions_spawn(
    cwd="/Users/tangbomao/.openclaw/workspace",  # ← 指向项目 workspace 根目录
    ...
)
```

### 2. attach 挂载（关键！）
```python
attachAs={"mountPath": "/Users/tangbomao/.openclaw/workspace"}  # ← 挂载 workspace
```

### 3. 输入明确
- Task ID
- 当前步骤（writing / review / export）
- 完成后要做什么（更新状态 / 触发下一步）

### 4. 禁止
- ❌ 不带 cwd 调用 sessions_spawn
- ❌ 不带 attachAs 调用 sessions_spawn
- ❌ main agent 兜底执行（必须 subagent 执行）

---

## End-to-End 验收标准

一次完整链路必须包含：

```
Heartbeat
→ 检测任务
→ 自动 dispatch（不是 main 执行）
→ subagent 读取 TASK-POOL
→ 执行任务
→ writer → review → export 自动推进
→ TASK-POOL 更新
→ 真实文件产出
```

**不满足任一项，都不算修复完成。**

---

## 修复完成定义

✅ subagent 协作链路跑通  
✅ 不依赖 main agent 兜底  
✅ 不依赖 Founder 提醒  
✅ 自动闭环成立  

---

## 核心原则

1. **单一调度入口**：所有周期任务由 Heartbeat 统一调度，不允许独立 cron
2. **可恢复**：任务错过不会永久丢失，下次触发时补做
3. **可补偿**：未执行的周期任务在下次触发时补偿执行

---

## 执行流程

### 0. 数据源统一（关键！）

**单一数据源（Single Source of Truth）**：
- TASK-POOL.md: `/Users/tangbomao/.openclaw/workspace/TASK-POOL.md`
- Execution Records: `/Users/tangbomao/.openclaw/workspace/memory/execution-records.json`

❌ 禁止：多个路径混用
✅ 必须：所有 agent 统一读取同一位置

---

### 1. Execution Record 加载（新增）

从文件加载执行记录：

```
位置: /Users/tangbomao/.openclaw/workspace/memory/execution-records.json

结构:
{
  "research-agent": {
    "last执行": "2026-03-16",
    "week_id": 12
  },
  "novel-v1": {
    "last执行": "2026-03-24",
    "date": "2026-03-24"
  }
}
```

### 2. Project Scan（项目扫描）

读取 Project Registry（从 TASK-POOL.md），识别所有 ACTIVE 项目：

| Project ID | Project Name | Status | Cycle |
|------------|--------------|--------|-------|
| hub-v1 | AI 独立站 | ACTIVE | NONE |
| sticker-v1 | 表情包工具 | ACTIVE | NONE |
| motionclean-v1 | MotionClean | ACTIVE | NONE |
| novel-v1 | 小说编辑部 | ACTIVE | DAILY |
| research-agent | 机会研究 | ACTIVE | WEEKLY |

### 3. Production Rule Detection（生产规则检测）

对每个项目识别周期类型：

- **DAILY**: 每日生产（如 novel-v1: 2篇/天）
- **WEEKLY**: 每周任务（如 research-agent: 3个/周）
- **MONTHLY**: 每月任务
- **NONE**: 无周期，仅任务驱动

### 4. Task Generation（任务生成）

#### 4.1 DAILY 项目检查

```markdown
novel-v1:
- 检查日期: 今日是否已执行 (last执行 date == today)
- 若已执行: 跳过
- 若未执行: 生成 2 个新任务 → 写入 TASK-POOL → 调度
```

#### 4.2 WEEKLY 项目检查（核心改进）

```markdown
research-agent:
- 计算当前 week_id: ISO week number (如 2026年第12周 = week_id: 12)
- 检查: 上次执行的 week_id == 当前 week_id?
- 若相同: 本周已执行，跳过
- 若不同: 本周未执行，立即触发（无论今天是周几）
```

**关键逻辑**：

| 上次执行 week_id | 当前 week_id | 动作 |
|------------------|--------------|------|
| 12 | 13 | ✅ 触发 |
| 13 | 13 | ⏭️ 跳过 |

#### 4.3 MONTHLY 项目检查

```markdown
- 检查: 上次执行的月份 == 当前月份?
- 若相同: 本月已执行，跳过
- 若不同: 本月未执行，立即触发
```

### 5. Project Task Check（专项任务检查）

检查所有项目是否存在：
- 待执行但超过 24h 未推进
- BLOCKED 状态超过 48h
- REVISION 状态超过 24h

### 6. Dispatch Execution（调度执行）—— 核心改动

**内容链路**：
```
lead-novel → story-editor → writer → review-editor → export
```

**自动判断**：
- 若有等待中的任务 → 调度下一个 Agent
- 若无 → 跳过

**执行方式（必须调用）**：

```python
# 伪代码示例
from sessions_spawn 或 subagents

# 1. 检查等待任务
waiting_tasks = get_tasks_by_status("WAITING")

for task in waiting_tasks:
    # 2. 确定下一个 Agent
    next_agent = determine_next_agent(task)
    
    # 3. 真正调用执行（不是只描述！）—— 必须配置环境！
    sessions_spawn(
        agentId=next_agent,
        task=task.description,
        runtime="subagent",
        cwd="/Users/tangbomao/.openclaw/workspace",  # ← 必须指向 TASK-POOL 所在目录
        attachAs={"mountPath": "/Users/tangbomao/.openclaw/workspace"}  # ← 挂载 workspace
    )
    
    # 4. 更新任务状态为 IN_PROGRESS
    update_task_status(task.id, "IN_PROGRESS")
```

**⚠️ 关键配置（必须！）：**

| 参数 | 值 | 原因 |
|------|-----|------|
| `cwd` | `/Users/tangbomao/.openclaw/workspace` | TASK-POOL.md 所在目录 |
| `attachAs.mountPath` | `/Users/tangbomai/.openclaw/workspace` | subagent 需要访问父目录文件 |

❌ 禁止：不带 cwd/attachAs 调用 sessions_spawn
✅ 必须：配置正确的工作目录

**关键原则**：
- ❌ 禁止：只描述"应该调度"，不实际调用
- ❌ 禁止：输出"需要执行"后等待用户确认
- ✅ 必须：`sessions_spawn()` 或 `subagents(action=steer)` 真正触发执行
- ✅ 必须：检测到任务后立即自动 dispatch，不等待
- ✅ 完成必须导致推进（completion must cause progression）

**自动推进流程（强制）**：
```
检测到 WAITING 任务 → 立即调用 sessions_spawn → 更新状态为 IN_PROGRESS
```

**不允许中断**：Heartbeat 执行过程中不允许暂停等待人工确认

### 7. Execution Record 更新（执行后）

每次任务执行后，更新记录：

```json
{
  "research-agent": {
    "last执行": "2026-03-24",
    "week_id": 12,
    "产出": 3
  }
}
```

### 8. System Status Logging（状态记录）

记录到日志：

```markdown
## Heartbeat Log

**执行时间**: 2026-03-24 09:00
**扫描项目数**: 5
**DAILY 任务生成**: 2 (novel-v1)
**WEEKLY 任务触发**: 1 (research-agent, week_id: 12 → 13)
**状态**: SUCCESS / FAILED
**异常**: [如有]
```

---

## 异常处理

| 情况 | 处理 |
|------|------|
| DAILY 项目未触发 | 立即生成任务 + 调度 |
| WEEKLY 本周未执行 | 立即触发（补偿机制） |
| 任务卡在中间 | 推进到下一环节 |
| BLOCKED 超过 48h | 标记风险，上报 Founder |
| 导出失败 | 重新导出 |

---

## 触发条件

| 时间 | 任务 |
|------|------|
| **每天 09:00**（北京时间） | 任务调度（DAILY/WEEKLY/MONTHLY 生产） |
| **每天 18:00**（北京时间） | Daily Report 生成 + 发送 |

**执行后**: 自动执行 Execution Record 加载 → Project Scan → Task Generation → Dispatch → Record Update → Report

---

## 9. Daily Report 生成（18:00 触发）

### 触发逻辑
- 每次 Heartbeat 18:00 执行时自动触发
- 检查今日是否已有报告：`memory/REPORT-YYYY-MM-DD.md`
- 若已有 → 跳过
- 若无 → 生成报告
- **若是周日** → 额外生成 Weekly OS Report

### 报告内容要求

**必须包含**：
1. **Time Validation**：确认所有产出完成时间 = 今日
2. **项目进展**：所有 ACTIVE 项目状态（novel-v1 / hub-v1 / sticker-v1 / motionclean-v1 / research-agent）
3. **DAILY 生产**：novel-v1 今日产出（目标 vs 实际）
4. **WEEKLY 生产**：research-agent 本周产出（如有）
5. **TASK-POOL 状态**：待执行/执行中/已完成数量
6. **风险提示**：BLOCKED / 超过 24h 未推进的任务
7. **Top 3**：
   - 🔥 今日最重要进展
   - ⚠️ 最大风险
   - 🎯 明日唯一优先事项

### Sunday Special: Weekly OS Report

若是周日（weekday == 6），生成完整版 Weekly OS Report：

**额外包含**：
- Project Board 完整状态
- Agent Status 汇总
- System Health 完整检查
- Gateway Summary（来自 gateway-lite-v1）
- Bottleneck Summary
- Kill / Scale 建议
- 下周优先任务

**文件**：`memory/WEEKLY-OS-REPORT-WW-YYYY-MM-DD.md`

### 执行方式

```python
# 18:00 Heartbeat 时调用
sessions_spawn(
    agentId="report-generator",
    task=f"生成 {today} 的 Daily Report",
    runtime="subagent",
    cwd="/Users/tangbomao/.openclaw/workspace",
    attachAs={"mountPath": "/Users/tangbomao/.openclaw/workspace"}
)
```

### 输出
- 文件：`memory/REPORT-YYYY-MM-DD.md`
- 发送：飞书消息给 Founder（channel=feishu）

### 禁止
- ❌ 不发空报告
- ❌ 不使用历史任务冒充今日产出
- ❌ 不跳过 Time Validation

---

## 10. OS Radar + Skills Gap Review（每周一触发）

### 触发逻辑
- 每周一 09:00 触发（与生产任务调度并行）
- 检查 `memory/os-radar/` 和 `memory/skills-gap/` 是否有本周记录

### OS Radar（向外看）

**频率**：每周至少 1 个对象

**格式**：
```markdown
# OS Radar - [对象名]

1. 它是什么
2. 最值得借鉴的点（≤3条）
3. 对我们的启发
4. 选择判断：fork / 轻改 / 自研 / 暂不做
5. 最小接入点
6. 对 AI Company OS 的价值
7. 当前优先级：P0 / P1 / P2
```

**当前研究队列**：
1. ClawManager ✅（本周完成）
2. OpenClaw Office ✅（本周完成）
3. Skills Registry ✅（本周完成）
4. AI Gateway Lite ✅（本周完成）

### Skills Gap Review（向内看）

**频率**：每周至少 1 次更新

**格式**：表格
```markdown
| skill / capability | 当前缺口说明 | 影响项目 | 借现成/轻改/自研 | 最小接入点 | 优先级 |
```

**要求**：
- 必须可执行，不停留在"技能要补齐"
- 必须回答"现在最小能做什么"
- 每次更新标记：新增 / 补齐 / 推进中

### 禁止
- ❌ 只研究外部，不盘点内部缺口
- ❌ 只说"缺很多能力"，不形成清单

---

## 核心原则（更新版）

1. **单一调度入口**: 所有周期任务由 Heartbeat 统一调度
2. **基于周期判断**: WEEKLY 基于 week_id，不是星期几
3. **可恢复**: 错过则补，不丢任务
4. **可补偿**: 任何周期未执行，下次触发时补偿
5. **不依赖对话**: Cron 触发后自动执行全流程
6. **不中断**: 任务完成后立即推进下一步
7. **可追溯**: 所有操作记录到 Execution Record + TASK-POOL
8. **每日汇报**: 18:00 自动生成 Daily Report
9. **外部研究**: OS Radar 每周至少 1 个对象
10. **内部盘点**: Skills Gap Review 每周更新
