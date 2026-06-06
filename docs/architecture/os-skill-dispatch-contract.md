---
version: v0.46.5
status: Active
last_updated: 2026-06-05
---
# OS Skill Dispatch Contract

> Version: 0.46.4.1
> Status: Active
> Last Updated: 2026-06-05

---

## 四类文件边界定义

| 文件类型 | 路径 | 所有者 | 读写规则 |
|---------|------|--------|----------|
| Skill Definition | os-skills/<domain>/<skill>.yaml | Hermes/Founder | Read by all, write by Hermes/Founder |
| Task Card | private/dispatch/inbox/*.yaml | Hermes CEO | Read/Write by Hermes only |
| Capability Request | private/capability-requests/inbox/*.yaml | Hermes → Executor | Executor reads, Hermes writes |
| Executor Result | private/capability-requests/outbox/*.yaml | Executor | Executor writes, Hermes reads |

---

## Executor Read-Only Inbox Rule

核心约束（硬规则，不可绕过）：

Executor may read inbox/ and private/capability-requests/inbox/ request files, but MUST NOT delete, move, overwrite, or modify them. The inbox request file is the OS canonical source of truth. Executor may only write results to outbox/, errors to failed/, and temporary files to its own workdir/ (if applicable).

违规处理：
- 若 Executor 删除/修改 inbox 文件 → inbox_file_preserved = false → Test FAIL
- 若再次发生 → Working Copy Pattern 立即升级为 P0 必做项

正确的 Executor 流程：
1. Read: 从 inbox/ 读取 request 文件
2. Execute: 执行任务
3. Write: 只写结果到 outbox/
4. Done: 通知 Hermes，inbox 文件由 Hermes CEO 负责清理

---

## Dispatch Task Card Schema

id: TC-xxx
status: pending | running | waiting-review | done | blocked
created_by: ceo
created_at: ISO-8601
title: "任务标题"
required_skills:
  - skill-name
skill_manifest_refs:
  - os-skills/<domain>/<skill>.yaml
input_ref: private/capability-requests/inbox/REQ-xxx.yaml
expected_output_ref: private/capability-requests/outbox/RES-xxx.yaml
assigned_to: executor-name
notes: "执行备注"

---

## Capability Request Schema

id: REQ-xxx
task_card_ref: TC-xxx
created_by: hermes-ceo
created_at: ISO-8601
skill: skill-name
input:
  # 任务输入参数
instructions: |
  详细任务指令
output_ref: private/capability-requests/outbox/RES-xxx.yaml

---

## Executor Result Schema

id: RES-xxx
request_ref: REQ-xxx
task_card_ref: TC-xxx
status: completed | failed | partial
generated_at: ISO-8601
executor:
  type: openclaw | hermes | claude-code | codex
  agent: agent-name
  model: model-name
  token_usage:
    input: N
    output: N
    total: N
  duration_ms: N
content:
  # 技能相关字段
errors: []
notes: "执行备注"

---

## 验证 Checklist（每次 Executor 测试必须通过）

- [ ] openclaw_direct_writeback_pass = true — outbox 文件真实落盘
- [ ] hermes_readback_pass = true — Hermes 能从文件系统读取
- [ ] inbox_file_preserved = true — inbox 原始文件仍然存在
- [ ] inbox_content_unchanged = true — inbox 内容未被修改（before/after hash 一致）
- [ ] result_schema_valid = true — result yaml 符合 schema
- [ ] executor_type_confirmed = true — 确认是 Executor 直接写回，非 Hermes 代写

任一未通过 → Test FAIL，Working Copy Pattern 立即升级为 P0

---

## P0/P1/P2 Roadmap — AI Company OS Executor 线

### P0-A：Executor Contract 验证 ✅ (v0.46.4.1 完成)

目标：验证 OpenClaw 能作为 Executor 执行文本型 skill

完成标准：
- [x] openclaw_direct_writeback_pass = true — outbox 文件真实落盘
- [x] hermes_readback_pass = true — Hermes 能从文件系统读取
- [x] inbox_file_preserved = true — inbox 原始文件仍存在
- [x] inbox_content_unchanged = true — before/after hash 一致
- [x] result_schema_valid = true — result 符合 schema

P0-A 明确不做：自动轮询、并行 worker、权限隔离、API Gateway、数据库、UI

---

### P0-B：Manual Two-Task Parallel Trial（v0.46.4.2，下一步）

目标：验证两个任务能并行存在、分别执行、分别写回、状态互不覆盖

验证项：
- [ ] Task Card × 2 并存在于 dispatch/inbox/
- [ ] Request × 2 并存在于 capability-requests/inbox/
- [ ] OpenClaw 分别执行，结果写回 outbox/
- [ ] outbox 结果 × 2 都能被 Hermes 读取
- [ ] 两个 result schema 都正确
- [ ] dispatch 状态机能追踪每个任务

P0-B 明确不做：Cron Poller、sessions_spawn 自动并发、Dispatch 状态机自动化

---

### P1：Dispatch Worker Lite（v0.46.5 / v0.47）

目标：OpenClaw 从手动触发升级为像员工一样接活

包含：
1. OpenClaw Cron Poller — 定时扫描 inbox，发现任务自动领取
2. sessions_spawn / subagent 并行 — 多任务真正并行执行
3. Dispatch 状态机 — inbox → assigned → running → waiting-review → done/blocked
4. Agent Compatibility Matrix 生效 — Task Card 引用 skill 时自动选可用 executor
5. required_skills 强约束 — Task Card 必须引用 os-skills/skill-registry.yaml 中存在的 skill
6. Writeback Review Flow — outbox result → CEO review → memory candidate / asset / evidence 判断

触发条件：P0-B 全部通过 + Founder 确认

---

### P2：Agent Army Operating System（v0.48+）

目标：Founder 只面对一个 CEO Agent，后台 Agent 军团基于 OS 规则自动运行

包含：
1. Local Capability Gateway — OpenClaw / Hermes / Claude / Codex 统一接口
2. Tool Adapter Layer — ComfyUI / SD / TTS / 视频 / 音频，通过适配器接入 OS
3. 权限隔离 — inbox: read-only，outbox: write-only，workdir: read/write
4. 自动 Context Pack Builder — 按 task_type / skills / A/B 层 / sensitivity 组装上下文
5. 多产品线自动运行 — AI 音乐 / AI 小说 / OS 系统层 / GitHub / 内容增长

明确不进入 OS Core：
- ❌ ComfyUI 直接内置
- ❌ TTS 直接内置
- ❌ 视频生成工具直接内置
- ✅ 这些全部通过 Tool Adapter Layer 接入

触发条件：P1 全部稳定运行 + Founder 单独批准

---

## OS Core 边界定义

AI Company OS Core（只管这些）：
- Dispatch / Task Routing
- Executor 军团管理
- Memory / Skill Registry
- Governance Rules
- Evidence / Asset Layer

Tool Adapter Layer（外部接入）：
- ComfyUI / SD
- TTS / 音频
- 视频生成
- 未来新工具

---

## Governance Rule: P0/P1/P2 Continuity

任何新模块进入 P0 / MVP 时，必须同时记录：
1. 当前 P0 只验证什么
2. P1 下一步扩展什么
3. P2 长期完整形态是什么
4. 当前明确不做什么
5. 什么时候进入下一阶段（触发条件）
6. 沉淀位置：roadmap / architecture doc / memory candidate

变更记录：此规则已进入 Company Memory Core candidate 待 Founder 审批
