# checkpoint-resume-v1 — Project Specification

**版本**: 1.0
**更新时间**: 2026-03-31
**状态**: P0 执行中

---

## 一、目标

把 AI Company OS 从"超时后重来"升级为"超时后从最近有效进度继续运行"。

---

## 二、P0 范围（3 类 checkpoint）

| 类型 | 描述 | 状态 |
|------|------|------|
| task_init_checkpoint | Task Card 创建后保存 | ✅ P0 |
| structure_checkpoint | 大纲/结构完成后保存 | ✅ P0 |
| draft_progress_checkpoint | 写作过程中按 scene 保存 | ✅ P0 |
| review_ready_checkpoint | review 前保存 | ⏳ P1 |
| export_ready_checkpoint | export 前保存 | ⏳ P1 |

---

## 三、数据结构

### 统一 checkpoint schema

```json
{
  "checkpoint_id": "novel-23-structure-2026-03-31T01-12-00",
  "project_id": "novel-v1",
  "task_id": "novel-23",
  "stage": "structure_ready",
  "checkpoint_type": "structure_checkpoint",
  "payload_ref": "novel-v1/outlines/novel-23-outline.md",
  "progress_pct": 30,
  "created_by": "story-editor",
  "created_at": "2026-03-31T01:12:00+08:00",
  "next_agent": "writer",
  "resume_from": "outline_completed",
  "is_latest": true,
  "validation_status": "valid"
}
```

### TASK-POOL 新增字段

```yaml
autonomy_status: autonomous_passed | resumed | main_rescue
main_rescue_used: true | false
last_checkpoint_ref: checkpoint_id
resume_count: 0
timeout_stage: null | lead-novel | story-editor | writer | review-editor | export
business_completed: true | false
autonomy_completed: true | false
```

---

## 四、存储结构

```
novel-v1/checkpoints/
├── task-init/           # 任务初始化
│   └── <task_id>-task-init-<ts>.json
├── structure/           # 结构/大纲
│   └── <task_id>-structure-<ts>.json
└── draft-progress/     # 写作进度
    └── <task_id>-draft-<ts>.json
```

---

## 五、timeout 分级配置

| Agent | 默认 timeout |
|-------|--------------|
| lead-novel | 3 min |
| story-editor | 5 min |
| writer | 8 min |
| review-editor | 3 min |
| export | 2 min |

---

## 六、Resume Flow

```
timeout 检测
  ↓
查找最近 valid checkpoint
  ↓
判断 stage 是否允许 resume
  ↓
从 resume_from 继续
  ↓
若失败 → fallback / main rescue
  ↓
main rescue 必须标记:
  - autonomy_status = main_rescue
  - main_rescue_used = true
```

---

## 七、P0 验收标准

1. novel-v1 主链路已建立 3 类 checkpoint 点位
2. writer 超时后能从最近 checkpoint 继续
3. main rescue 时不再整条链重做
4. 日报可区分：business_completed / autonomy_completed / main_rescue_used
5. 至少 1 次真实 resume 成功案例

---

## 八、后续 P1

- review_ready_checkpoint
- export_ready_checkpoint
- 更细粒度 resume
- 更完整状态呈现