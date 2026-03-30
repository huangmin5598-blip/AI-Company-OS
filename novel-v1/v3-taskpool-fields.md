# TASK-POOL 字段变更清单 (v3 - P0 实现)

---

## 一、新增字段总览

| 字段名 | 类型 | 用途 | 阶段 |
|--------|------|------|------|
| `task_mode` | string | 执行模式 (standard/lite/split/segmented) | P0 |
| `timeout_count` | number | 超时次数 | P0 |
| `last_timeout_at` | timestamp | 最后超时时间 | P0 |
| `fallback_mode` | string | 降级模式记录 | P0 |
| `last_agent` | string | 最后执行的 agent | P0 |
| `next_agent` | string | 下一个执行的 agent | P0 |
| `handoff_ready` | boolean | 是否可自动推进 | P0 |
| `block_reason` | string | 阻塞原因 | P0 |
| `degradation_flag` | boolean | 是否进入降级状态 | P1 |
| `partial_output_ref` | string | partial 文件引用 | P1 |
| `partial_output_status` | string | partial 是否可用 | P1 |
| `resume_from` | string | 断点续写位置 | P1 |
| `last_completed_scene` | string | 最后完成的 scene | P1 |
| `story_editor_progress` | object | split 恢复进度 | P1 |
| `export_status` | string | 导出状态 | P1 |
| `final_output_path` | string | 最终文档路径 | P1 |
| `execution_record_ref` | string | 执行记录引用 | P1 |

---

## 二、核心字段定义 (P0)

### task_mode

```yaml
task_mode: standard  # standard | lite | split | segmented
```

**说明**：当前任务执行模式，用于分级控制。

---

### timeout_count

```yaml
timeout_count: 2
```

**说明**：当前任务累计超时次数。

**判定规则**：
- 0 = 无超时
- 1-2 = 可重试
- 3 = 切换模式
- ≥4 = blocked

---

### last_timeout_at

```yaml
last_timeout_at: "2026-03-27T10:30:00Z"
```

**说明**：记录最后一次超时的时间戳，用于分析超时规律。

---

### fallback_mode

```yaml
fallback_mode: "standard→lite"
```

**说明**：记录降级路径，用于分析系统稳定性。

---

### last_agent / next_agent

```yaml
last_agent: writer
next_agent: review-editor
```

**说明**：记录执行链路，用于自动推进判断。

---

### handoff_ready

```yaml
handoff_ready: true
```

**说明**：是否满足自动推进条件。

**触发条件**：
- 当前 agent 任务完成
- 输出包含 next_agent
- 未 blocked

---

### block_reason

```yaml
block_reason: "writer timeout ≥4 次"
```

**说明**：记录阻塞原因，用于系统介入判断。

---

## 三、降级相关字段 (P1)

### degradation_flag

```yaml
degradation_flag: true
```

**触发条件（满足任一）**：
1. 连续 3 次进入 lite 模式
2. 任一节点 timeout_count ≥ 3
3. 同一 task 连续 fallback_required
4. 同一项目 24h 内多节点 blocked

**自动保守策略**：
- lead-novel → 强制 lite
- story-editor → 强制 lite 或 split
- writer → 强制 segmented + shorter target
- review-editor → 分批 Composition

---

## 四、断点恢复相关字段 (P1)

### partial_output_ref

```yaml
partial_output_ref: novel-17-scene3-partial.json
```

**说明**：引用独立 partial 文件，避免 TASK-POOL 膨胀。

---

### partial_output_status

```yaml
partial_output_status: usable  # usable | unusable | consumed
```

**说明**：
- `usable`: 部分产出可用，可续写
- `unusable`: 部分产出不可用，需从头
- `consumed`: 部分产出已被使用

---

### resume_from

```yaml
resume_from: "scene_3_beat_2"
```

**说明**：下次从断点继续的位置。

---

### last_completed_scene

```yaml
last_completed_scene: scene_2
```

**说明**：记录已完成的 scene，用于判断进度。

---

### story_editor_progress (split 恢复)

```yaml
story_editor_progress:
  current_phase: phase_2
  completed_phases: [phase_1]
  recoverable: true
```

**说明**：story-editor split 模式的恢复进度。

**phase 定义**：
- phase_1: Story Bible
- phase_2: Scene 列表
- phase_3: 写作卡片
- phase_4: 版权预判

---

## 五、export 相关字段 (P1)

### export_status

```yaml
export_status: success  # pending | success | failed
```

**说明**：导出状态，用于闭环追踪。

---

### final_output_path

```yaml
final_output_path: "novel-v1/manuscripts/2026-03-27/novel-17-黎明之前.docx"
```

**说明**：最终输出文件路径，用于归档。

---

### execution_record_ref

```yaml
execution_record_ref: "execution-records.json"
```

**说明**：引用执行记录，用于闭环追踪。

---

## 六、字段使用示例

### 示例 1: 新任务创建 (lead-novel 阶段)

```yaml
task_id: novel-17
project_id: novel-v1
status: handoff_ready
task_mode: standard
timeout_count: 0
last_agent: lead-novel
next_agent: story-editor
handoff_ready: true
degradation_flag: false
```

---

### 示例 2: writer 阶段 (含 timeout + partial)

```yaml
task_id: novel-17
status: running
task_mode: lite
timeout_count: 2
last_timeout_at: "2026-03-27T10:30:00Z"
fallback_mode: "standard→lite"
last_agent: writer
next_agent: review-editor
handoff_ready: false
partial_output_ref: novel-17-scene3-partial.json
partial_output_status: usable
resume_from: scene_3_beat_2
last_completed_scene: scene_2
degradation_flag: true
```

---

### 示例 3: 任务完成 (export 后)

```yaml
task_id: novel-17
status: done
task_mode: lite
timeout_count: 2
fallback_history: ["standard→lite", "lite→segmented"]
last_agent: review-editor
next_agent: null
handoff_ready: true
degradation_flag: true
export_status: success
final_output_path: "novel-v1/manuscripts/2026-03-27/novel-17-黎明之前.docx"
execution_record_ref: "execution-records.json"
```

---

## 七、TASK-POOL 更新规则

### 自动更新场景

| 场景 | 更新字段 |
|------|----------|
| agent 完成 | last_agent, next_agent, handoff_ready, status |
| timeout 发生 | timeout_count, last_timeout_at, fallback_mode |
| partial 输出 | partial_output_ref, partial_output_status, resume_from |
| scene 完成 | last_completed_scene |
| degradation 触发 | degradation_flag |
| export 完成 | export_status, final_output_path, execution_record_ref, status=done |

### 禁止行为

- ❌ 禁止在 partial_output 中直接塞入大段文本
- ❌ 禁止 export 后不更新 TASK-POOL
- ❌ 禁止跳过任何更新步骤

---

## 八、字段持久化位置

| 数据类型 | 存储位置 |
|----------|----------|
| 任务状态字段 | TASK-POOL.md |
| partial 内容 | ~/.openclaw/workspace/novel-v1/partials/ |
| 执行记录 | memory/execution-records.json |
| 最终文档 | novel-v1/manuscripts/YYYY-MM-DD/ |

---

## 九、字段验证检查

每次 TASK-POOL 更新时，必须验证：

1. ✅ `task_id` 存在且唯一
2. ✅ `status` 符合状态机定义
3. ✅ `next_agent` 存在且正确（除非 status=done）
4. ✅ `handoff_ready` 与 `next_agent` 一致
5. ✅ `timeout_count` 与 `fallback_mode` 一致
6. ✅ `export_status` 与 `final_output_path` 一致（若 status=done）