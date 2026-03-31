# System Health — Control Center V1 模块

**版本**: 1.0
**更新时间**: 2026-03-31
**模块**: Control Center V1 - Module 7 (最后一个)

---

## 一、模块说明

System Health 是 control-center-v1 P0 的第七个模块，负责展示系统整体健康状态。

**数据源**：
- `HEARTBEAT.md` → 心跳配置
- `heartbeat.log` → 心跳执行记录
- `execution-records.json` → 执行状态
- `gateway-lite-v1` → Gateway 运行状态
- Registry / Memory Layer → 存储层状态
- export 相关记录 → 导出状态

---

## 二、字段定义

| 字段 | 描述 | 必填 | 数据来源 |
|------|------|------|----------|
| heartbeat_status | Heartbeat 状态 | ✅ | heartbeat.log |
| cron_status | Cron 状态 | ✅ | openclaw cron list |
| gateway_status | Gateway 状态 | ✅ | gateway-lite |
| registry_status | Registry 状态 | ✅ | execution-records |
| memory_layer_status | Memory Layer 状态 | ✅ | memory 文件 |
| export_status | Export 状态 | ✅ | 导出记录 |
| active_warning_count | 活跃 Warning 数 | - | gateway-lite |
| blocked_count | Blocked 项目数 | - | TASK-POOL |
| failed_count | Failed 任务数 | - | execution-records |
| last_incident | 最近事件 | - | 系统记录 |

---

## 三、健康状态说明

### 状态定义

| 状态 | 描述 | 颜色标记 |
|------|------|----------|
| healthy | 正常运行 | 🟢 |
| warning | 存在警告，但不影响运行 | 🟡 |
| critical | 严重异常，需要立即处理 | 🔴 |

### 检查项

| 检查项 | healthy 条件 | warning 条件 | critical 条件 |
|--------|--------------|--------------|----------------|
| Heartbeat | 最近 24h 内执行成功 | > 24h 未执行 | > 48h 未执行 |
| Cron | 所有任务 status=ok | 有 error 任务 | 50%+ 任务 error |
| Gateway | 可访问，无 error | 有 warning | 无法访问 |
| Registry | 可写 | - | 不可写 |
| Memory Layer | 可写 | - | 不可写 |
| Export | 最近导出成功 | - | 最近导出失败 |

---

## 四、Daily 简版

### 输出格式

```markdown
## System Health

### 整体状态: 🟢 Healthy

| 模块 | 状态 | 备注 |
|------|------|------|
| Heartbeat | 🟢 OK | 最近: 2026-03-31 09:00 |
| Cron | 🟡 Warning | 3 个 error (金融摘要相关) |
| Gateway | 🟢 OK | 成本记录正常 |
| Registry | 🟢 OK | 可写 |
| Memory | 🟢 OK | 可写 |
| Export | 🟢 OK | 最近: 2026-03-31 |

### 异常汇总
- **Active Warning**: 0
- **Blocked**: 1 (motionclean-v1)
- **Failed**: 0

### Founder 需关注
- **金融摘要 cron error** (待修复)
```

---

## 五、Weekly 完整版

### 输出格式

```markdown
# System Health — Week 15, 2026-03-31

## 整体状态: 🟢 Healthy

### 核心模块健康情况

| 模块 | 状态 | 最后检查 | 备注 |
|------|------|----------|------|
| Heartbeat | 🟢 OK | 2026-03-31 09:00 | 每日正常执行 |
| Cron | 🟡 Warning | 2026-03-31 08:30 | 3 个 error (finance) |
| Gateway | 🟢 OK | 2026-03-31 | 成本记录正常 |
| Registry | 🟢 OK | 2026-03-31 | 可写，正常 |
| Memory | 🟢 OK | 2026-03-31 | 可写，正常 |
| Export | 🟢 OK | 2026-03-31 | docx 导出正常 |
| checkpoint-resume | 🟢 OK | 2026-03-31 | P0 验收通过 |
| routing-layer | 🟢 OK | 2026-03-31 | 冲突试验通过 |

### 异常趋势

| 指标 | Week 14 | Week 15 | 趋势 |
|------|---------|---------|------|
| Active Warning | 2 | 0 | ↓ |
| Blocked | 1 | 1 | - |
| Failed | 3 | 0 | ↓ |

### 本周 Incident 摘要

| 日期 | 类型 | 模块 | 描述 | 状态 |
|------|------|------|------|------|
| 2026-03-30 | error | Cron | 金融摘要 cron error | 待修复 |
| 2026-03-30 | error | Cron | 外围市场动态 error | 待修复 |
| 2026-03-28 | blocked | Project | motionclean-v1 资源问题 | 已解决 |

### 需要优先处理

1. **金融摘要 cron error** - finance-analyst 模型问题已修复，待验证
2. **外围市场动态 cron error** - 待检查

### 建议

- ✅ checkpoint-resume-v1 P0 已完成，可减少 main_rescue
- ✅ routing-layer-v1 冲突处理已验证
- ⏳ 建议：修复金融相关 cron error

---

## 六、数据读取逻辑

```python
# 伪代码

def read_system_health():
    # 1. Heartbeat 状态
    heartbeat_log = read_heartbeat_log()
    heartbeat_status = "healthy" if heartbeat_log.last_execution.within_24h else "warning"
    
    # 2. Cron 状态
    cron_list = openclaw_cron_list()
    error_count = sum(1 for c in cron_list if c.status == "error")
    cron_status = "critical" if error_count > len(cron_list)*0.5 else "warning" if error_count > 0 else "healthy"
    
    # 3. Gateway 状态
    gateway_status = "healthy" if gateway.reachable else "critical"
    
    # 4. Registry 状态
    registry_status = "healthy" if registry.writable else "critical"
    
    # 5. Memory Layer 状态
    memory_status = "healthy" if memory.writable else "critical"
    
    # 6. Export 状态
    export_status = "healthy" if export.last_success.within_24h else "warning"
    
    # 7. 统计
    active_warning = gateway.active_warnings
    blocked = task_pool.blocked_count
    failed = execution_records.failed_count
    
    # 8. 整体状态
    if critical_count > 0:
        overall = "critical"
    elif warning_count > 0:
        overall = "warning"
    else:
        overall = "healthy"
    
    return {
        "overall_status": overall,
        "heartbeat_status": heartbeat_status,
        "cron_status": cron_status,
        "gateway_status": gateway_status,
        "registry_status": registry_status,
        "memory_layer_status": memory_status,
        "export_status": export_status,
        "active_warning_count": active_warning,
        "blocked_count": blocked,
        "failed_count": failed,
        "last_incident": incidents.latest
    }
```

---

## 七、验收标准

| 标准 | 状态 |
|------|------|
| Founder 一眼看清系统健康状态 | ✅ |
| 能看到 heartbeat/cron/gateway/registry/memory/export 状态 | ✅ |
| 能看到 warning/blocked/failed 汇总 | ✅ |
| 数据来源清晰，复用现有系统记录 | ✅ |
| P0 信息层完整闭环 | ✅ |

---

## 八、与前面模块的关系

| 模块 | System Health 关联 |
|------|-------------------|
| Project Board | blocked 项目数 |
| Agent Status | failed 任务关联 |
| Gateway Summary | gateway_status |
| Capability Overview | 能力缺口关联 |
| Routing Summary | 异常路由关联 |
| CEO Escalation Summary | escalation 汇总 |

System Health 是所有模块的"底层基础设施"视角。

---

## 九、control-center-v1 P0 总结

### 完成状态

**✅ control-center-v1 P0 信息层已完成**

### 7 个模块清单

| # | 模块 | 状态 | 数据源 |
|---|------|------|--------|
| 1 | Project Board | ✅ | TASK-POOL, execution-records |
| 2 | Agent Status | ✅ | openclaw, CAPABILITY-REGISTRY |
| 3 | Gateway Summary | ✅ | gateway-lite |
| 4 | Capability Overview | ✅ | CAPABILITY-REGISTRY |
| 5 | Routing Summary | ✅ | ROUTING-RULES, conflict-log |
| 6 | CEO Escalation Summary | ✅ | ROUTING-RULES, execution-records |
| 7 | System Health | ✅ | heartbeat.log, cron, registry |

### 输出形式

| 类型 | 时间 | 内容 |
|------|------|------|
| Daily | 18:00 | 简版（7 模块摘要）|
| Weekly | 周日 20:00 | 完整版（7 模块 + Bottleneck 分析）|

### 验收标准达成

- ✅ Founder 一眼看清系统
- ✅ 数据来源清晰，复用现有系统
- ✅ 区分 running/blocked/done
- ✅ 区分 idle/working/error
- ✅ 区分 healthy/warning/critical
- ✅ 可闭环输出 Daily/Weekly Report

---

## 十、下一阶段建议 (P1)

### 建议启动顺序

| 优先级 | 项目 | 目标 |
|--------|------|------|
| P1-1 | preflight-diagnostics-v1 | 实时健康检查 |
| P1-2 | evidence-dashboard-lite-v1 | 对外证据展示 |
| P1-3 | control-center-v1 P1 | 实时 Dashboard |

### P1 潜在扩展

- 实时 Web Dashboard
- 移动端通知
- 自动化告警
- 与飞书深度集成

---

## 十一、next_step

1. 整合到 Daily Report 18:00 输出中
2. 在周日 20:00 Heartbeat 中触发 Weekly 完整版
3. 更新 execution-records 中 control-center-v1 状态
