# Routing Rules — AI Company OS

**版本**: 1.2 (真实运行版)
**更新时间**: 2026-03-31
**状态**: P0 - 验证中

---

## 一、Message Routing（消息路由）

### 规则 1：Founder 输入分流

```
founder_input
  → 判断: on-demand / project / system
  → on-demand → CEO 直接响应
  → project → 进入项目池
  → system → 进入系统命令（heartbeat, report, status）
```

**route_reason**:
- on-demand: Founder 请求即时响应，不需要立项
- project: Founder 请求涉及项目执行，需要立项和调度
- system: Founder 请求是系统运维/查看类，不涉及业务执行

---

## 二、Task Routing（任务路由）

### 规则 4：next_agent 判定

| 阶段 | next_agent | route_reason |
|------|-----------|--------------|
| task_init | lead-novel / lead-hub / research-agent | 项目启动需要 Lead 规划 |
| planning | story-editor | 需要结构设计能力 |
| drafting | writer | 需要内容生产 |
| reviewing | review-editor | 需要质量控制 |
| exporting | (自动导出) | 产出需要持久化 |

---

## 三、Exception Routing（异常路由）

### 规则 6：timeout 路由

```
timeout_event
  → 判断: checkpoint_available?
  → 有 checkpoint → resume_from_checkpoint
  → 无 checkpoint → fallback_agent 重试
  → fallback 失败 → main_rescue
```

---

## 四、真实命中案例验证

### 案例 1: founder_input → project (2026-03-31 novel-v1)

**触发**: Founder 要求"今天写两篇小说"
**路由过程**:
1. CEO 收到请求 → route_type = message
2. 判断 route_reason = "项目执行需求" → 命中 project
3. 分配到 novel-v1 → next_agent = lead-novel
4. lead-novel 创建 Task Card → 调度 story-editor

**验证结果**: ✅ 通过
- route_type = message
- route_reason = project
- next_agent = lead-novel

---

### 案例 2: timeout_event → resume (2026-03-31 novel-26)

**触发**: writer timeout (30s)
**路由过程**:
1. writer 超时 → route_type = exception
2. 检查 checkpoint_ref = "novel-26-structure-2026-03-31T08-11-03"
3. route_reason = "有 checkpoint 可复用" → 命中 resume_from_checkpoint
4. autonomy_status = resumed

**验证结果**: ✅ 通过
- route_type = exception
- route_reason = "有 checkpoint 可复用"
- checkpoint_ref = novel-26-structure-2026-03-31T08-11-03
- autonomy_status = resumed

---

### 案例 3: task_completed_event → memory / report (2026-03-31 novel-23)

**触发**: novel-23 写作完成
**路由过程**:
1. review-editor 标记 PASS → route_type = event
2. 写入 execution-records.json → 正式记录
3. 写入 memory/2026-03-31.md → 日常记录
4. route_reason = "任务完成，需要持久化 + 更新上下文"

**验证结果**: ✅ 通过
- route_type = event
- route_reason = "task_completed, 需要持久化"
- 写入 execution-records.json ✅
- 写入 memory/2026-03-31.md ✅

---

### 案例 4: 多项目冲突场景 (理论验证)

**触发**: novel-v1 和 research-agent 同时需要 tiger-coder
**路由过程**:
1. 两个项目同时请求 tiger-coder → route_type = exception
2. route_reason = "多项目冲突"
3. escalation_to = CEO → 需要 CEO 决策优先级

**验证结果**: ✅ 规则存在，待实际触发验证

---

## 五、显式字段清单

所有任务和事件必须包含以下字段：

| 字段 | 描述 | 必填 | 说明 |
|------|------|------|------|
| route_type | message / task / exception / event | ✅ | 路由类型 |
| route_reason | 路由原因说明 | ✅ | 为什么走这条路由 |
| next_agent | 下一个处理 Agent | ✅ | 下一个处理者 |
| fallback_agent | 失败后 fallback Agent | ✅ | 失败后的处理者 |
| escalation_to | 升级目标 | ✅ | 最终升级给谁 |
| current_stage | 当前阶段 | ✅ | task_init/planning/drafting/reviewing/exporting |
| checkpoint_ref | 最近 checkpoint（若有） | - | 用于 resume |
| autonomy_status | autonomous_passed / resumed / main_rescue | ✅ | 任务执行状态 |

---

## 六、Registry 字段

| 字段 | 值 |
|------|-----|
| current_stage | P0 |
| next_stage | P1 |
| owner | tiger |
| end_state | Routing Layer 显式规则完整，联动 control-center 展示 |
| freeze_rule | 完成 P1 前不冻结 |

---

## 七、验证状态

| 验证项 | 状态 | 案例 |
|--------|------|------|
| founder_input → project | ✅ 通过 | novel-v1 任务分配 |
| timeout_event → resume | ✅ 通过 | novel-26 超时恢复 |
| task_completed_event → memory | ✅ 通过 | novel-23 完成记录 |
| 多项目冲突 → CEO | ⚠️ 待触发 | - |

---

## next_step

- 等待更多真实案例验证
- 与 checkpoint-resume-v1 联动
- 与 control-center-v1 联动展示
