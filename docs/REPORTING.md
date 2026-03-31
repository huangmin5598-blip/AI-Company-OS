# REPORTING.md - 每日汇报系统

**版本**: 1.0
**用途**: 每日 18:00 自动生成并发送项目进展报告

---

## 核心原则

1. **不依赖 HEARTBEAT** - 独立运行
2. **不依赖任务触发** - 固定时间执行
3. **强制输出** - 即使无产出也必须输出报告
4. **完全解耦** - HEARTBEAT(09:00) + Reporting(18:00)

---

## 触发时间

- **Cron**: 每天 18:00 北京时间 (10:00 UTC)
- **触发方式**: openclaw cron job

---

## 报告模板

```markdown
# 📊 Daily Operating Report

## 🫀 Heartbeat Status
- Scheduled: 09:00
- Executed: YES / NO
- Status: SUCCESS / FAILED
- Notes: （如失败原因）

---

## 📈 Production KPI

| Project | Target | Actual | Status |
|---------|--------|--------|--------|
| novel-v1 | 2 | X | OK / FAILED |
| xxx-v1 | X | X | OK / FAILED |

---

## 🗂 TASK-POOL Status

| Status | Count |
|--------|------|
| Pending | X |
| In Progress | X |
| Completed | X |
| Blocked | X |

关键任务（最多列3个）：
- Task ID - 状态 - 卡点

---

## 📦 Deliverables（真实产出）—— 强制今日过滤

**过滤规则**：Completed Date = today（必须！）

> ⚠️ 只统计今日完成的任务，历史完成不算！

今日实际产出：

- docx：
  - xxx.docx
- code：
  - xxx.tsx
- page：
  - xxx.html

**筛选逻辑**：
```python
# 伪代码
today = datetime.now().date()
today_completed = [t for t in tasks 
                   if t.status == "COMPLETED" 
                   and t.completed_date.date() == today]
```

⚠️ 如果没有产出必须写：

👉 No deliverables produced

---

## 🚨 Bottleneck & Issues

今日主要问题：

1. xxx
2. xxx

原因：

- 模型问题 / 流程问题 / 调度问题

---

## 🔧 Failure & Recovery

是否发生失败：YES / NO

类型：

- TRIGGER / FLOW / EXECUTION / EXPORT

是否执行恢复：

- Recovery: YES / NO
- Compensation: YES / NO

---

## 🧠 Key Insights（必须有）

今天系统层面的结论：

- 1句话总结问题或优化点
```

---

## 实现逻辑

### 1. 数据采集

从以下位置读取：
- TASK-POOL.md - 任务状态统计
- HEARTBEAT.md - 检查今日是否执行
- 项目目录 - 统计实际产出

### 2. KPI 计算

| 项目 | Target | 统计方式 |
|------|--------|----------|
| novel-v1 | 2篇/天 | 检查今日完成的小说数量 |
| sticker-v1 | 9张/天 | 检查今日生成的模板数量 |

### 3. 状态统计

- Pending: 状态为"待执行"的任务
- In Progress: 状态为"执行中"的任务
- Completed: 状态为"已完成"的任务
- Blocked: 状态为"阻塞"的任务

### 4. 产出统计

检查以下目录：
- `/Users/tangbomao/.openclaw/workspace/novel-v1/manuscripts/`
- `/Users/tangbomao/workspace/sticker-templates/`

### 5. 输出渠道

- 发送至 Feishu 用户
- 或写入飞书文档

---

## 异常处理

| 情况 | 处理 |
|------|------|
| 无任务 | 输出 "No deliverables produced" |
| HEARTBEAT 未执行 | 标记为 FAILED |
| 任务全部完成 | 标记为 SUCCESS |
| 发生阻塞 | 标记并列出卡点 |

---

## Cron 配置

```bash
openclaw cron add "0 10 * * *" --session main --label reporting
```

说明：
- 10:00 UTC = 18:00 北京时间
- 专门用于 Reporting

---

## 验证标准

1. ✅ 手动执行能输出完整报告
2. ✅ 即使无任务也能输出报告
3. ✅ 包含所有必填字段
4. ✅ 18:00 自动输出（明日验证）

---

## 禁止行为

❌ 不允许将 Reporting 写入 HEARTBEAT  
❌ 不允许"没有数据就不输出"  
❌ 不允许依赖人工触发  
❌ 不允许输出不完整结构
