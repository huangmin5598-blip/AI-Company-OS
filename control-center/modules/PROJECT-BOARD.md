# Project Board — Control Center V1 模块

**版本**: 1.0
**更新时间**: 2026-03-31
**模块**: Control Center V1 - Module 1

---

## 一、模块说明

Project Board 是 control-center-v1 P0 的第一个模块，负责展示所有项目的状态概览。

**数据源**：
- `TASK-POOL.md` → 项目列表、状态、阶段
- `execution-records.json` → 项目产出记录、自主状态

---

## 二、字段定义

| 字段 | 描述 | 必填 | 数据来源 |
|------|------|------|----------|
| project_id | 项目唯一标识 | ✅ | TASK-POOL |
| project_name | 项目名称 | ✅ | TASK-POOL |
| project_lead | 项目负责人 | ✅ | TASK-POOL |
| status | 运行状态 | ✅ | TASK-POOL (ACTIVE/PAUSED) |
| current_stage | 当前阶段 | ✅ | TASK-POOL (MVP/ITERATION) |
| cycle | 运行周期 | - | TASK-POOL (DAILY/WEEKLY/-) |
| target | 目标产出 | - | TASK-POOL |
| last_completed_task | 最近完成任务 | - | execution-records |
| autonomy_status | 自主状态 | - | execution-records |
| main_rescue_used | 是否使用 main_rescue | - | execution-records |
| last_updated | 最后更新时间 | ✅ | TASK-POOL |

---

## 三、状态定义

### 运行状态 (status)

| 状态 | 描述 |
|------|------|
| ACTIVE | 运行中 |
| PAUSED | 暂停 |
| DONE | 已完成 |

### 当前阶段 (current_stage)

| 阶段 | 描述 |
|------|------|
| MVP | 最小可行产品开发 |
| ITERATION | 迭代中 |
| PLANNING | 规划中 |
| VALIDATION | 验证中 |

### 自主状态 (autonomy_status)

| 状态 | 描述 |
|------|------|
| autonomous_passed | 自主完成 |
| resumed | 从 checkpoint 恢复 |
| main_rescue | 需 main 介入 |

---

## 四、Daily 简版

### 输出格式

```markdown
## Project Board

| Project | Lead | Stage | Status | Today Output |
|---------|------|-------|--------|--------------|
| novel-v1 | lead-novel | ITERATION | ACTIVE | 2 篇 |
| hub-v1 | lead-hub | MVP | ACTIVE | - |
| gateway-lite-v1 | tiger-coder | MVP | ACTIVE | - |
| control-center-v1 | tiger-coder | MVP | ACTIVE | - |
```

---

## 五、Weekly 完整版

### 输出格式

```markdown
# Project Board — Week 15, 2026-03-31

## 项目总览

| # | Project | Lead | Stage | Cycle | Last Updated | Total Tasks | Completed |
|---|---------|------|-------|-------|--------------|-------------|-----------|
| 1 | novel-v1 | lead-novel | ITERATION | DAILY | 2026-03-31 | 4 | 4 |
| 2 | hub-v1 | lead-hub | MVP | - | 2026-03-16 | 3 | 3 |
| 3 | sticker-v1 | lead-sticker | MVP | - | 2026-03-16 | 3 | 3 |
| 4 | motionclean-v1 | lead-motionclean | MVP | - | 2026-03-20 | 5 | 5 |
| 5 | gateway-lite-v1 | tiger-coder | MVP | - | 2026-03-30 | 0 | 0 |
| 6 | control-center-v1 | tiger-coder | MVP | - | 2026-03-30 | 0 | 0 |
| 7 | capability-registry-v1 | tiger-coder | P0 | - | 2026-03-31 | 0 | 0 |
| 8 | routing-layer-v1 | tiger-coder | P0 | - | 2026-03-31 | 0 | 0 |

## 项目详情

### novel-v1 (小说编辑部)
- **状态**: ACTIVE
- **阶段**: ITERATION
- **周期**: DAILY (2篇/天)
- **最近产出**: novel-24 (2026-03-31)
- **autonomy_status**: main_rescue

### hub-v1 (AI独立站)
- **状态**: ACTIVE
- **阶段**: MVP
- **最近产出**: 完成 MVP 规划

...
```

---

## 六、读取逻辑

### 从 TASK-POOL.md 读取项目列表

```python
# 伪代码

def read_project_board():
    # 1. 读取 TASK-POOL 项目注册表
    projects = parse_task_pool_project_registry()
    
    # 2. 读取 execution-records 获取产出状态
    records = read_execution_records()
    
    # 3. 合并数据
    board = []
    for project in projects:
        record = records.get(project.id)
        board.append({
            "project_id": project.id,
            "project_name": project.name,
            "project_lead": project.lead,
            "status": project.status,
            "current_stage": project.stage,
            "cycle": project.cycle,
            "target": project.target,
            "last_completed_task": record.last_task if record else None,
            "autonomy_status": record.autonomy_status if record else None,
            "main_rescue_used": record.main_rescue_used if record else False,
            "last_updated": project.last_updated
        })
    
    return board
```

---

## 七、验收标准

| 标准 | 状态 |
|------|------|
| Founder 能一眼看清当前项目列表与状态 | ✅ |
| 数据来源清晰，复用现有系统数据 | ✅ |
| 能区分 running/blocked/done 状态 | ✅ |
| 能区分 autonomy_status | ✅ |
| 能作为后续模块基础 | ✅ |

---

## 八、next_step

实现 Daily Report 中的 Project Board 模块，整合到 heartbeat 18:00 触发逻辑中。
