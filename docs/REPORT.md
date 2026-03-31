# REPORT.md - Daily Operating Report

**版本**: 1.0
**触发时间**: 每日 18:00（北京时间）
**用途**: 生成并输出 Daily Operating Report

---

## 核心原则

1. **自动执行**: 触发后立即执行，不等待指令
2. **基于数据**: 所有信息必须从 TASK-POOL.md 和 execution-records.json 读取
3. **完整输出**: 必须包含所有Required sections

---

## 执行流程

### 1. 数据收集

读取以下文件：
- `TASK-POOL.md` → 获取项目状态和任务列表
- `memory/execution-records.json` → 获取周期执行记录
- `memory/YYYY-MM-DD.md`（今日）→ 获取今日事件

### 2. 项目状态扫描

从 TASK-POOL.md 提取 Project Registry：

| Project ID | Project Name | Status | Stage | Cycle | Target |
|------------|--------------|--------|-------|-------|--------|
| hub-v1 | AI 独立站 | ACTIVE | MVP | - | - |
| sticker-v1 | 表情包工具 | ACTIVE | MVP | - | - |
| novel-v1 | 小说编辑部 | ACTIVE | ITERATION | DAILY | 2 |
| motionclean-v1 | MotionClean | ACTIVE | MVP | - | - |

### 3. 周期任务执行状态

检查 execution-records.json：

```json
{
  "research-agent": { "last执行": "2026-03-24", "week_id": 13 },
  "novel-v1": { "last执行": "2026-03-24", "date": "2026-03-24", "产出": 2 },
  "sticker-v1": { "last执行": "2026-03-23", "date": "2026-03-23", "产出": 9 }
}
```

### 4. 任务完成情况

从 TASK-POOL.md 提取今日完成的任务（Completed Date = 今日）：

| Task ID | 项目 | 描述 | 完成时间 |
|---------|------|------|----------|
| novel-7 | novel-v1 | 短篇 #7：豪门弃妇逆袭 | 2026-03-23 |
| novel-8 | novel-v1 | 短篇 #8：互换人生 | 2026-03-23 |

### 5. KPI 评估

| 项目 | Target | Actual | Rate | Status |
|------|--------|--------|------|--------|
| novel-v1 | 2 | 2 | 100% | ✅ |
| research-agent | 3/周 | 3 | 100% | ✅ |

---

## 报告输出格式（Required）

### 一、项目进展（Project Level）

按每个 ACTIVE 项目汇报：

```
## 📊 [项目名]

**当前阶段**: [MVP/验证/迭代]
**今日进展**: [一句话]
**状态**: [正常/风险/阻塞]
```

### 二、产出汇总（Output Summary）

| 项目 | 今日产出 | 类型 |
|------|----------|------|
| novel-v1 | 2 篇短篇 | 小说 |
| research-agent | 3 个机会 | Opportunity Card |

### 三、系统状态（System Status）

- TASK-POOL 任务数：X
- BLOCKED 任务：X（如有）
- 周期执行状态：正常

### 四、风险与问题（Risk）

列出所有风险点：
- BLOCKED 任务及原因
- 项目阻塞情况

### 五、明日重点（Next）

明天优先执行的 1-3 件事：

---

## 输出要求

1. **必须发送**: 报告生成后必须推送到用户（Feishu）
2. **格式**: Markdown
3. **时间**: 18:00 触发后 5 分钟内完成

---

## 异常处理

| 情况 | 处理 |
|------|------|
| 数据文件不存在 | 标记错误，记录日志 |
| 任务状态异常 | 标记风险，上报 |
| 报告生成失败 | 记录错误，返回简报 |

---

## 核心原则

> 不是流水账，而是帮助 Founder 做决策的报告。

输出必须：
- ✅ 有项目状态
- ✅ 有产出数据
- ✅ 有风险提醒
- ✅ 有明日建议
