# 🔄 Run Flow — AI Company OS

**Version**: 1.0 (External Preview)
**Updated**: 2026-04-01
**Purpose**: External display / GitHub / Landing page / Demo recording

---

## 核心工作流

### novel-v1 小说生产流水线

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  lead-novel │───▶│ story-editor│───▶│    writer   │───▶│review-editor│
│  (选题/调度) │    │  (大纲设计) │    │  (正文写作) │    │  (质量审核) │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │                  │
       ▼                  ▼                  ▼                  ▼
   Task Card         Outline            Manuscript         PASS/REVISION
   生成任务卡          设计大纲             完成初稿            质量验收
```

**每日产出**: 2 篇短篇小说
**周期**: 每日 08:00 触发

---

## Task Card 流转记录

### 2026-03-31 任务流转

| Task ID | 创建时间 | 阶段 | Agent | 状态 |
|---------|----------|------|-------|------|
| novel-26 | 08:11 | completed | lead-novel → story-editor → writer → review-editor | ✅ PASS |
| novel-27 | (待生成) | - | - | - |

### 2026-03-30 任务流转

| Task ID | 创建时间 | 阶段 | Agent | 状态 |
|---------|----------|------|-------|------|
| novel-23 | 01:01 | completed | lead-novel → story-editor → writer → review-editor | ✅ PASS |
| novel-24 | 01:02 | completed | lead-novel → story-editor → writer → review-editor | ✅ PASS |
| novel-25 | 07:55 | completed | lead-novel → story-editor → writer → review-editor | ✅ PASS |

---

## Task Card 示例

### novel-26 Task Card

```markdown
# Task Card: novel-26

**Project**: novel-v1
**Created**: 2026-03-31 08:11
**Deadline**: 2026-03-31 18:00

## Task
写作短篇小说《密室解剖师》

## Requirements
- 字数: 2000-3000 字
- 类型: 悬疑/推理
- 风格: 紧凑悬疑

## Acceptance Criteria
- [x] 完整的故事结构
- [x] 悬疑氛围营造
- [x] 人物塑造立体
- [x] 结局有反转

## Workflow
1. lead-novel 创建任务卡
2. story-editor 设计大纲
3. writer 写作正文
4. review-editor 审核
```

---

## 典型工作流模式

### 模式 1: 直线流转 (80%)

```
Lead → Editor → Writer → Review → ✅ 完成
```

### 模式 2: 返工流转 (15%)

```
Lead → Editor → Writer → Review → ❌ REVISION
  ↑                                    │
  └──────────── 返工 writer ←──────────┘
```

### 模式 3: 升级流转 (5%)

```
Lead → Editor → Writer → Review → ⚠️ BLOCKED
  ↑                                       │
  └──────────── 升级 CEO 决策 ←──────────┘
```

---

## 调度统计

| 指标 | 值 |
|------|-----|
| **今日调度次数** | 8 次 |
| **直线流转成功率** | 80% |
| **返工率** | 15% |
| **升级率** | 5% |
| **平均完成时间** | 2-4 小时 |

---

## 数据来源

- `novel-v1/TASK-CARDS/` → 任务卡记录
- `novel-v1/manuscripts/` → 产出物
- `novel-v1/outlines/` → 大纲记录

---

*Generated: 2026-04-01 04:07 (Asia/Shanghai)*