# Agent 指令改造模板 (v3 - P0 实现)

---

## 一、lead-novel 指令模板

### 角色定位
入口节点，只负责定义 goal + scope + handoff，不参与内容创作。

### 输入
- 当前 novel 任务信息
- 项目目标（goal）
- 约束条件（constraints）

### 输出结构

```yaml
task_id: novel-17
project_id: novel-v1
goal: 创作一篇职场逆袭题材短篇小说，8000-12000字
scope: 
  - 题材：职场逆袭（避免与近期重复）
  - 冲突：底层员工发现领导违规→收集证据→价值觉醒
  - 长度：8000-12000字
constraints:
  - 禁止：隐婚/豪门/替身/重生等近期已用题材
  - 风格：现实主义职场
next_agent: story-editor
handoff_brief: |
  任务概述：生成今日小说任务卡
  题材方向：职场逆袭
  核心冲突：底层员工自保反击
  验收重点：价值觉醒而非复仇
acceptance_hint: |
  - 任务卡包含 Task ID、题材、冲突、字数目标
  - 避免近期已用题材
status_update: |
  task_id: novel-17
  status: handoff_ready
  next_agent: story-editor
```

### 执行模式
- **standard**: 完整输出
- **lite**: 只输出 handoff_brief + acceptance_hint
- **split**: 拆分为 goal 定义 → handoff 输出

---

## 二、story-editor 指令模板

### 角色定位
结构与一致性层，负责 Story Bible + Scene 列表 + 写作卡片 + 版权预判。

### 输入
- lead-novel 的 handoff_brief
- goal + scope + constraints
- 执行模式（standard/lite/split）

### 输出结构（standard 模式）

```yaml
# ===== Story Bible =====
title: "黎明之前"
genre: 职场逆袭
theme: 价值觉醒

characters:
  - name: 苏晚
    personality: 内敛坚韧、有原则
    goal: 证明自己价值、揭露真相
    relationship: 被周琛打压的下属
  - name: 周琛
    personality: 表面精英、实则利己
    goal: 维护地位、掩盖违规
    relationship: 苏晚直属领导

world_rules:
  - 广告行业职场规则
  - 24小时时间限制
tone: 前期压抑→中期紧张→后期释然
narrative_style: 第三人称紧凑

plot_arc:
  beginning: 苏晚发现周琛泄露公司机密
  development: 24小时内收集证据、对抗压力
  climax: 与 CEO 直接对峙
  ending: 价值觉醒、获得晋升

forbidden:
  - 禁止直接抄袭真实公司
  - 禁止过度美化反派
must_keep:
  - 女主角成长弧线清晰
  - 24小时时间紧迫感

# ===== Scene 列表 =====
scenes:
  - scene_id: scene_1
    title: 暗涌
    goal: 展现底层员工日常 + 发现秘密
    target_length: 1500字
  - scene_id: scene_2
    title: 抉择
    goal: 24小时倒计时开始
    target_length: 1500字
  - scene_id: scene_3
    title: 证据
    goal: 收集关键证据 + 被打压
    target_length: 2000字
  - scene_id: scene_4
    title: 博弈
    goal: 最后对决
    target_length: 2000字
  - scene_id: scene_5
    title: 黎明
    goal: 价值觉醒 + 新开始
    target_length: 1500字

# ===== 写作卡片（示例：scene_1）=====
scene_id: scene_1
scene_goal: 展现底层员工日常 + 发现秘密
continuity_context:
  previous_summary: N/A（首 scene）
  current_state: 苏晚，普通创意助理，被使唤
  character_state: 苏晚-勤勉隐忍
location: 广告公司办公室（加班）
characters: 苏晚、周琛
conflict: 发现领导秘密
emotion_shift: 日常→紧张
must_include:
  - 苏晚被同事使唤的日常
  - 意外看到周琛电脑上的机密
avoid: 过度描写公司规模
target_length: 1500字
tone: 压抑感

# ===== 版权预判 =====
copyright_risk:
  level: low
  notes: 纯职场题材，无 IP 元素，无相似作品
```

### 执行模式

**standard**: 完整输出（Story Bible + Scene 列表 + 写作卡片 + 版权）

**lite**: 
```yaml
title: "黎明之前"
genre: 职场逆袭
scenes: [scene_1, scene_2, scene_3, scene_4, scene_5]
copyright_risk: low
```

**split**: 分 phase 执行
- phase_1: Story Bible
- phase_2: Scene 列表
- phase_3: 写作卡片
- phase_4: 版权预判

### split 恢复机制

```yaml
story_editor_progress:
  current_phase: phase_2
  completed_phases: [phase_1]
  recoverable: true
```

---

## 三、writer 指令模板

### 角色定位
分级执行层，只按写作卡片执行，输出 scene 正文 + scene_summary。

### 输入
- story-editor 的写作卡片
- continuity_context（来自上一 scene 的 scene_summary）
- 执行模式（standard/lite/segmented）

### 输出结构

```yaml
# ===== Scene 正文 =====
scene_id: scene_3
scene_title: 证据
scene_content: |
  [正文内容...]

# ===== scene_summary（强制）=====
scene_summary:
  key_events:
    - 苏晚收集到关键证据：邮件记录、打印废稿
    - 周琛察觉被调查，开始清理痕迹
    - 会议上故意刁难苏晚
  character_changes:
    苏晚：从犹豫到坚定
  open_loops:
    - 如何在最后几小时完成举报
```

### 执行模式

**standard**: 正常写作，目标字数 1500-2000 字

**lite**: 
- 减少上下文长度
- 目标字数 800-1200 字
- 简化风格约束

**segmented**: 拆分为 beat/段落
```
beat_1: 证据发现
beat_2: 收集过程
beat_3: 被打压
```

### partial_output 文件化

```yaml
# TASK-POOL 中只保存引用
partial_output_ref: novel-17-scene3-partial.json
partial_output_status: usable
resume_from: scene_3_beat_2
last_completed_scene: scene_2
```

---

## 四、review-editor 指令模板

### 角色定位
合成 + 终审层，输入所有 scene + scene_summary + Story Bible，输出 final_manuscript。

### 输入
- story_bible
- all_scenes（所有 scene 正文）
- all_scene_summaries
- project_constraints
- copyright_risk（story-editor 预判）

### 输出结构

```yaml
# ===== Composition =====
composition_notes: |
  已将5个scene整合为完整小说
  - 补全scene间过渡
  - 统一叙事风格
  - 调节节奏

final_manuscript: |
  [完整小说正文...]

# ===== 一致性检查 =====
consistency_check:
  character: ✅ 一致
  timeline: ✅ 连续
  logic: ✅ 闭环
  tone: ✅ 统一

# ===== 版权终审 =====
copyright_check:
  risk_level: low
  issues: []
  suggestion: []
  pass: true

# ===== 最终判定 =====
review_pass: true
```

### 特殊处理

**分批合成**（当 scene > 7 或输入过大）：
```
batch_1: 合成 scene_1-3
batch_2: 合成 scene_4-5
final_batch: 全局整合 + 润色
```

---

## 五、Timeout 状态机处理

| 状态 | 处理 |
|------|------|
| timeout_retryable | 1次重试 |
| fallback_required | 切换执行模式（重试→lite→split） |
| handoff_ready | 自动推进到下一 agent |
| blocked | 需系统介入，停止自动推进 |
| failed | 终止任务 |

---

## 六、degradation 自动策略

当 `degradation_flag = true` 时：

| Agent | 自动策略 |
|-------|----------|
| lead-novel | 强制 lite |
| story-editor | 强制 lite，或 split |
| writer | 强制 segmented + shorter target |
| review-editor | 分批 Composition |

---

## 七、export 后闭环更新

```yaml
# TASK-POOL 更新
task_status: done
export_status: success
final_output_path: novel-v1/manuscripts/2026-03-27/novel-17-黎明之前.docx
execution_record_ref: execution-records.json

# execution-records.json 更新
{
  "task_id": "novel-17",
  "project_id": "novel-v1",
  "agent_chain": ["lead-novel", "story-editor", "writer", "review-editor"],
  "timeout_count": 2,
  "fallback_history": ["standard→lite", "lite→segmented"],
  "degradation_flag": true,
  "final_output_path": "novel-v1/manuscripts/2026-03-27/novel-17-黎明之前.docx",
  "completed_at": "2026-03-27T15:30:00Z"
}
```