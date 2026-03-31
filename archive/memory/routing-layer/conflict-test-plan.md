# Routing-Layer-V1 冲突试验方案

**版本**: 1.0
**更新时间**: 2026-03-31
**状态**: 受控小试验（P0 并行）

---

## 一、试验背景

routing-layer-v1 的基础规则（founder_input→project, timeout→resume, task_completed→memory）已验证通过。

现在需要验证**下一层能力**：多项目冲突处理。

---

## 二、冲突类型定义

### 类型 1：共享 Agent 冲突

**定义**: 两个项目同时请求同一个关键 Agent

**触发场景**:
- novel-v1 需要 tiger-coder（gateway-lite 维护）
- hub-v1 需要 tiger-coder（独立站开发）
- 两个任务同时进入队列

**示例**:
```
任务 A: novel-v1 → 需要 tiger-coder (gateway-lite 维护)
任务 B: hub-v1 → 需要 tiger-coder (独立站开发)
时间: 同一 Heartbeat 周期
结果: 冲突
```

### 类型 2：优先级冲突

**定义**: 高优先级任务与普通任务同时进入

**触发场景**:
- system task（Daily Report 生成）与 project task（novel-v1 写作）同时进入
- system task 优先

**示例**:
```
任务 A: system → Daily Report (priority: high)
任务 B: novel-v1 → writer (priority: normal)
时间: 同一 Heartbeat 周期
结果: 优先级冲突
```

---

## 三、处理策略

### 策略 1：Queue（队列）

**适用**: 共享 Agent 冲突
**规则**: 先到先服务，后面的进入队列等待
**示例**:
```
任务 A (先到) → tiger-coder → 执行
任务 B (后到) → queue[tiger-coder] → 等待 A 完成
```

### 策略 2：Delay（延迟）

**适用**: 优先级冲突
**规则**: 低优先级任务延迟执行，高优先级先执行
**示例**:
```
任务 A (high) → tiger-coder → 立即执行
任务 B (normal) → delay 5min → 等待 A 完成后再执行
```

### 策略 3：Escalate（升级）

**适用**: 复杂冲突无法自动处理
**规则**: 升级到 CEO 决策
**示例**:
```
任务 A 和 B 都无法自动判定优先级
→ escalation_to = CEO
→ CEO 决策谁先执行
```

### 策略 4：Reject（拒绝）

**适用**: 资源明显不足
**规则**: 直接拒绝并记录
**示例**:
```
任务 B → 资源不足 → reject → 记录 reason
→ 通知 project_lead
```

---

## 四、冲突检测逻辑

```python
# 伪代码

def detect_conflict(task_a, task_b):
    # 类型 1: 共享 Agent 冲突
    if task_a.required_agent == task_b.required_agent:
        return {
            "type": "shared_agent",
            "agent": task_a.required_agent,
            "tasks": [task_a.id, task_b.id],
            "strategy": "queue"
        }
    
    # 类型 2: 优先级冲突
    if task_a.priority != task_b.priority:
        return {
            "type": "priority",
            "high_priority": max(task_a.priority, task_b.priority),
            "tasks": [task_a.id, task_b.id],
            "strategy": "delay"
        }
    
    return None
```

---

## 五、试验成功标准

| 标准 | 定义 | 验证方式 |
|------|------|----------|
| 冲突识别 | 系统能识别出 2 类冲突 | 人工触发后日志显示 |
| 策略应用 | 按 queue/delay 策略处理 | 任务执行顺序验证 |
| 记录完整 | 冲突信息写入日志 | 检查冲突日志文件 |
| 升级触发 | 复杂场景能升级到 CEO | 人工标记复杂场景 |

---

## 六、最小试验路径

### 步骤 1：模拟共享 Agent 冲突

**操作**:
1. 手动创建两个任务，都需要 tiger-coder
2. 观察系统如何处理

**预期**:
- 先到的任务执行
- 后到的任务进入队列

### 步骤 2：模拟优先级冲突

**操作**:
1. 手动创建 system task + project task
2. 观察系统如何处理

**预期**:
- system task 优先执行
- project task 延迟

### 步骤 3：验证升级逻辑

**操作**:
1. 创建无法自动判定的场景
2. 观察是否升级到 CEO

**预期**:
- escalation_to = CEO
- 等待 CEO 决策

---

## 七、输出文件

**冲突日志**: `memory/routing-layer/conflict-log.md`

```
## 冲突记录

### 2026-03-31 共享 Agent 冲突试验
- 类型: shared_agent
- Agent: tiger-coder
- 任务: [task_A, task_B]
- 策略: queue
- 结果: ✅ 通过
```

---

## 八、约束

**不要做**:
- 多项目全量并发
- 复杂资源池调度
- 动态抢占
- 复合冲突系统

**只做**:
- 最小 2 类冲突
- 受控试验
- 记录验证

---

## 九、与 control-center-v1 的关系

- control-center-v1 P0 继续推进，不因这个试验停下
- 冲突试验是**并行小试验**，不是主线
- 试验成功后，冲突处理能力可接入 control-center 展示
