# Business Guarantee Rules — Minimum Business Execution Guarantee

**Version**: 1.0
**Created**: 2026-04-01
**Owner**: CEO (main)
**Purpose**: Real project line minimum execution guarantee mechanism

---

## 一、核心原则

1. **真实项目线必须有独立发车机制** - 不再只靠 heartbeat 顺带触发
2. **heartbeat 只是时间信号** - 真正的业务保障由 business cron 负责
3. **业务优先于 OS 能力建设** - 冲突时真实项目线优先
4. **最低保障不等于高负载** - 目标是不断档、不掉线
5. **所有动作必须可审计** - 能回答"为什么没发车"

---

## 二、适用范围

| 类型 | 示例项目 | 保障级别 |
|------|----------|----------|
| 内容型 | novel-v1, 文章项目, 短剧脚本 | HIGH |
| 研究型 | research-agent, 机会挖掘, 竞品研究 | MEDIUM-HIGH |
| 产品型 | hub-v1, sticker-v1, MVP 项目 | MEDIUM |
| 运营型 | 内容分发, 渠道实验, 增长验证 | MEDIUM |

**不适用于**: OS 能力建设项目、纯系统维护任务、单次临时 system task

---

## 三、当前真实项目最低保障规则

| project_id | project_type | minimum_frequency | minimum_output_unit | cron_trigger | business_priority | allowed_skip_conditions | fallback_mode |
|------------|--------------|-------------------|---------------------|--------------|-------------------|------------------------|----------------|
| **novel-v1** | 内容型 | 每日 1 篇 | 1 篇短篇小说 | novel-daily | HIGH | 显式记录原因后允许 | lite / resume |
| **research-agent** | 研究型 | 每周 3 次 | 1 个 Opportunity Card | research-weekly | MEDIUM-HIGH | 连续一周无进展不允许 | skip with reason |
| **hub-v1** | 产品型 | 每周 1 次 | 1 次明确推进动作 | product-weekly | MEDIUM | 长期无动作不允许 | 记录阻塞原因 |
| **sticker-v1** | 产品型 | 每周 1 次 | 1 次明确推进动作 | product-weekly | MEDIUM | 长期无动作不允许 | 记录阻塞原因 |

---

## 四、任务状态标准化

| Status | Description | Must Record |
|--------|-------------|-------------|
| **scheduled** | 按业务规则，本次应该发车 | - |
| **created** | 任务已创建 | task_id, created_at |
| **dispatched** | 任务已送入项目链路 | dispatch_to_agent |
| **running** | 任务执行中 | start_time |
| **completed** | 业务结果完成 | output_summary |
| **blocked** | 任务被阻塞 | blocked_reason |
| **skipped** | 本次被显式跳过 | skip_reason (必须记录) |
| **rescued** | 原执行失败但 rescue 补回 | rescue_reason |

**禁止**: "今天没跑，但不知道为什么"

---

## 五、Business Cron Layer

### 当前已建立 (即将创建)

| Cron Job | Trigger Time | Responsibility |
|----------|--------------|----------------|
| novel-daily | 每天 08:00 | 创建当日 novel-v1 最低保障任务 |
| research-weekly | 每周一 09:00 | 创建 research-agent 周任务 |
| product-weekly | 每周一 09:00 | 创建 hub-v1/sticker-v1 周任务 |

### 职责定义

- **创建任务** - 按规则创建最低保障任务
- **送入项目池** - 不负责具体执行链路
- **记录审计** - 记录 task_created 事件

---

## 六、Audit Fields

所有最低保障任务必须记录：

```
{
  "task_id": "xxx",
  "project_id": "xxx",
  "expected_to_run": true/false,
  "task_created": true/false,
  "task_dispatched": true/false,
  "task_completed": true/false,
  "task_skipped": false/true,
  "skip_reason": "optional",
  "blocked_reason": "optional",
  "rescue_used": false/true,
  "rescue_reason": "optional"
}
```

---

## 七、与双轨系统的关系

### 优先级规则

1. **先确保** 真实项目线的最低保障任务已创建
2. **再分配** 剩余精力给 OS 能力建设项目
3. **如果资源不足**:
   - 真实项目线允许降级执行
   - 但不允许完全不发车

### 核心原则

> OS 线可以慢一点  
> 业务线不能凭空消失

---

## 八、角色职责

| Role | Responsibility |
|------|----------------|
| **CEO / main** | 拍板规则、决定优先级冲突、处理特殊跳过批准、主持周度 review |
| **lead-os** | 检查机制是否生效、检查"应发车但没发车"、报告双轨冲突 |
| **项目 Lead** | 接收任务、保证进入链路、如需跳过必须显式记录 |

---

## 九、Daily / Weekly Report 结构

### A. 真实项目线 (必须分开报告)

- 今日应发车项目
- 今日已创建任务
- 今日已完成产出
- 今日 skipped / blocked / rescued 情况

### B. OS 能力建设线

- 今日新增能力
- 今日机制推进
- 今日系统收口
- 今日证据层更新

---

## 十、P0 执行清单

- [x] 最低保障规则表已输出
- [ ] 建立独立 business cron 清单 (novel-daily, research-weekly, product-weekly)
- [ ] 至少接入当前 3 类项目 (novel-v1, research-agent, hub-v1)
- [ ] 审计字段与状态定义
- [ ] 更新日报/周报结构
- [ ] 完成 1 次真实"最低保障任务创建"验证

---

## Registry

| Field | Value |
|-------|-------|
| document_type | business-guarantee-rules |
| version | 1.0 |
| created | 2026-04-01 |
| owner | CEO (main) |
| status | P0 - In Progress |

---

*This document defines the minimum business execution guarantee for real project lines.*