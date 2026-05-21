# 最小验收测试用例 (v3 - P0 验证)

---

## 一、测试目标

验证在 **存在 timeout / fallback / 降级** 情况下，系统是否仍能自动完成完整闭环。

---

## 二、测试用例清单

### 测试 1: timeout 不中断流程

| 项目 | 内容 |
|------|------|
| **用例 ID** | TC-001 |
| **场景** | writer 超时 2 次 |
| **预期行为** | 自动切换到 lite 模式，继续执行 |
| **验证点** | - timeout_count 更新为 2<br>- fallback_mode 记录 "standard→lite"<br>- 任务状态变为 running（非 blocked） |
| **成功标准** | 流程不中断，继续推进到 review |

---

### 测试 2: split 可恢复

| 项目 | 内容 |
|------|------|
| **用例 ID** | TC-002 |
| **场景** | story-editor split 执行，phase_2 超时 |
| **预期行为** | 下次执行从 phase_2 继续，不重复 phase_1 |
| **验证点** | - story_editor_progress.current_phase = phase_2<br>- story_editor_progress.completed_phases 包含 phase_1<br>- story_editor_progress.recoverable = true |
| **成功标准** | 不重复执行已完成 phase |

---

### 测试 3: writer 可断点续写

| 项目 | 内容 |
|------|------|
| **用例 ID** | TC-003 |
| **场景** | writer timeout，已产出 partial_output |
| **预期行为** | 下次执行从断点继续，而非全量重写 |
| **验证点** | - partial_output_ref 存在<br>- partial_output_status = usable<br>- resume_from 指向正确位置<br>- last_completed_scene 记录已完成的 scene |
| **成功标准** | 续写时引用 partial 内容，不重复已完成部分 |

---

### 测试 4: review 能输出完整小说（非拼接感）

| 项目 | 内容 |
|------|------|
| **用例 ID** | TC-004 |
| **场景** | 5 个 scene 完成后进入 review |
| **预期行为** | review-editor 输出整合后的完整小说 |
| **验证点** | - final_manuscript 存在且长度符合预期<br>- composition_notes 包含过渡说明<br>- consistency_check 各项通过<br>- scene 间无明显拼接痕迹 |
| **成功标准** | 输出是完整小说，非简单拼接 |

---

### 测试 5: export 后 TASK-POOL 自动收口

| 项目 | 内容 |
|------|------|
| **用例 ID** | TC-005 |
| **场景** | review 通过 + 版权通过 → export |
| **预期行为** | 自动更新 TASK-POOL + execution-records |
| **验证点** | - TASK-POOL: status = done<br>- TASK-POOL: export_status = success<br>- TASK-POOL: final_output_path 存在<br>- execution-records.json 包含本轮记录 |
| **成功标准** | 无人工干预下完成双更新 |

---

## 三、测试执行方式

### 方式 A: 模拟注入（推荐）

通过模拟 timeout/fallback 场景，验证系统响应：

```python
# 模拟 writer timeout 2 次
task.timeout_count = 2
task.fallback_mode = "standard→lite"
task.task_mode = "lite"
→ 验证系统自动切换模式
```

### 方式 B: 真实运行

使用 novel-v1 真实任务，观察系统行为：

```
1. 启动任务 novel-18
2. 注入 timeout（如限制 token 触发超时）
3. 观察 fallback 行为
4. 验证各节点响应
5. 检查最终闭环
```

---

## 四、验证检查点

| 阶段 | 检查点 | 验证方式 |
|------|--------|----------|
| lead-novel | handoff 输出格式 | 读取输出 YAML |
| story-editor | split phase 恢复 | 检查 story_editor_progress |
| writer | partial 输出 | 检查 partial 文件 |
| writer | scene_summary 传递 | 检查 continuity_context |
| review-editor | final_manuscript 输出 | 读取输出 |
| export | TASK-POOL 更新 | 检查状态字段 |
| export | execution-records 更新 | 检查 JSON 文件 |

---

## 五、成功判定

| 测试 ID | 验证项 | 通过条件 |
|---------|--------|----------|
| TC-001 | timeout 处理 | timeout_count 正确更新 + 模式切换 |
| TC-002 | split 恢复 | completed_phases 不重复 |
| TC-003 | 断点续写 | partial 可引用 + resume_from 正确 |
| TC-004 | 完整小说 | final_manuscript 整合无拼接感 |
| TC-005 | 自动收口 | TASK-POOL + execution-records 双更新 |

**通过率要求**: 5/5 (100%)

---

## 六、测试数据

### 测试任务 ID

```
novel-18 (测试用)
novel-19 (测试用)
```

### 测试场景

| 任务 | 注入场景 |
|------|----------|
| novel-18 | writer timeout 2 次 |
| novel-19 | story-editor split phase_2 超时 |

---

## 七、日志记录

每次测试需记录：

```yaml
test_id: TC-001
task_id: novel-18
injected_scenario: writer timeout 2次
expected_behavior: 自动切换 lite
actual_behavior: [实际观察]
passed: true/false
notes: [备注]
```

---

## 八、执行优先级

| 优先级 | 测试用例 | 理由 |
|--------|----------|------|
| 1 | TC-001 | 最常见场景 |
| 2 | TC-005 | 闭环验证最重要 |
| 3 | TC-003 | 减少重复劳动 |
| 4 | TC-002 | split 恢复关键 |
| 5 | TC-004 | 最终质量验证 |

---

## 九、测试工具

可使用 OpenClaw 的 exec 工具模拟：

```bash
# 检查 TASK-POOL 状态
grep "novel-18" TASK-POOL.md

# 检查 partial 文件
ls -la novel-v1/partials/

# 检查 execution-records
cat memory/execution-records.json
```

---

## 十、注意事项

1. **禁止优化测试**：测试目标是验证闭环，不是提升质量
2. **允许失败**：若系统无法自动闭环，记录问题并修复
3. **关注自动性**：验证点是"无需人工干预"
4. **重复验证**：关键测试需重复执行确保稳定性