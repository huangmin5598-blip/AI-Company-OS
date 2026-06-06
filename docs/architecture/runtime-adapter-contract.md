---
version: v0.46.5
status: Active
last_updated: 2026-06-05
---
# Runtime Adapter Contract

**Version:** v0.46.5-B0R
**Status:** Active
**Owner:** AI Company OS

---

## 1. Concept

AI Company OS owns Work Queue, State Machine, Quality Gate, Audit Packet, Skill Registry.
External agent frameworks are **Runtime Adapters**, not the OS control plane.

Each Runtime Adapter must implement this contract to be recognized by OS Work Queue.

---

## 2. Runtime Adapter Profile Schema

```yaml
adapter_id: string (unique identifier)
adapter_type: deterministic | coding-executor | agent-host | conversation-agent | future-extension

invocation_method: string (how OS calls this adapter)
worker_identity: string (OS layer worker identity, e.g. os-worker/local-script)

supports_parallel: boolean
supports_file_write: boolean
returns_session_id: boolean
supports_status_polling: boolean
supports_timeout: boolean

verification_status: declared | verified | partially_verified | failed | blocked
last_verified_at: ISO8601 timestamp
evidence_ref: string (path to verification evidence)

best_for: list[string]
not_good_for: list[string]
risk_level: LOW | MEDIUM | HIGH

limitations: list[string] (honest disclosure of known gaps)

input_contract: string (human-readable contract)
output_contract: string (human-readable contract)

audit_evidence_required: list[string]
```

---

## 3. Adapter Profiles

### 3.1 local_script_adapter

```yaml
adapter_id: local_script_adapter
adapter_type: deterministic
worker_identity: os-worker/local-script
invocation_method: os-worker daemon / python wrapper
supports_parallel: true
supports_file_write: true
returns_session_id: false
supports_status_polling: false
supports_timeout: true
verification_status: verified
last_verified_at: 2026-06-05
best_for:
  - 文件扫描 / 一致性检查
  - 确定性脚本执行
  - 快速验证 Work Queue 状态机
not_good_for:
  - 复杂对话任务
  - 需要模型推理的生成
risk_level: LOW
audit_evidence_required:
  - stdout / stderr
  - exit_code
  - output_file (if any)
  - execution_time_ms
  - attempt_id
  - worker_id
```

### 3.2 codex_adapter

```yaml
adapter_id: codex_adapter
adapter_type: coding-executor
invocation_method: openclaw acp run codex
verification_status: declared
best_for:
  - 代码修改 / 重构
  - Repo 操作
  - 脚本生成
risk_level: MEDIUM
limitations:
  - rate_limit 并发限制
  - 需要明确 step-by-step 指令
```

### 3.3 claude_code_adapter

```yaml
adapter_id: claude_code_adapter
adapter_type: coding-executor
invocation_method: openclaw acp run claude-code
verification_status: declared
# Same structure as codex_adapter
```

### 3.4 openclaw_adapter

```yaml
adapter_id: openclaw_adapter
adapter_type: agent-host / acp-launcher
invocation_method: openclaw agent --agent main --message "..."
verification_status: partially_verified
last_verified_at: 2026-06-05
evidence_ref: private/records/milestone-003-manual-two-task-dispatch-pass.md

best_for:
  - 多 agent 对话 / ACP routing
  - Skill ecosystem execution
  - Cron-triggered agent workflows

not_good_for:
  - 静默文件写入
  - 原生 OS Work Queue 扫描
  - Execution Envelope parsing

risk_level: HIGH

limitations:
  - no_native_os_queue
  - no_native_execution_envelope_parser
  - agent_turn_is_conversation_oriented
  - silent_file_execution_not_reliable_without_acp_wrapper
  - systemEvent treats tasks as heartbeats
```

### 3.5 paperclip_adapter (future)

```yaml
adapter_id: paperclip_adapter
adapter_type: task-queue-native
invocation_method: TBD
verification_status: blocked
note: "Future candidate for native task queue support"
```

---

## 4. Audit Evidence Requirements

Every task execution must produce Audit Evidence containing:

```yaml
audit_evidence:
  work_id: string
  attempt_id: string (format: WQ-{id}-A{attempt_number})
  worker_id: string
  runtime_adapter: string
  written_by: string (must be os-worker, not Hermes)
  
  queue_state_transitions:
    - inbox→claimed: {timestamp, claimed_by, attempt_id, lease_expires_at}
    - claimed→running: {timestamp, worker_id}
    - running→waiting_review: {timestamp, output_ref}
  
  execution_evidence:
    stdout: string
    stderr: string
    exit_code: number
    execution_time_ms: number
    output_file_written: boolean
  
  artifact_hashes:
    task_file_sha256: string
    input_ref_sha256: string
    output_ref_sha256: string
  
  hermes_executed_business_task: false
  
  bootstrap_execution: boolean (true if Step 1 bootstrap)
```

---

## 5. State Machine

```
inbox → claimed → running → waiting_review → done
                                         ↘ failed
```

**P0 Rule:** No running → done direct transition. All tasks must pass waiting_review.

**Lock Fields:**
- attempt_id: WQ-{id}-A{attempt_number}
- worker_id: os-worker-{adapter}-{instance}
- claimed_by: worker identity
- claimed_at: ISO8601
- lease_expires_at: ISO8601
- heartbeat_at: ISO8601 (updated every 30s by worker)
- retry_count: number
- max_retries: 3 (P0 default)

---

## Framework-Agnostic Principle (updated v0.46.5)

**Previous:** OpenClaw was described as the primary executor.

**Current:** AI Company OS uses a PLUGGABLE RUNTIME ADAPTER model.

OpenClaw is ONE implementation of Runtime Adapter. Codex, Claude Code, local_script, and future frameworks are OTHERS.

AI Company OS does NOT bind to any specific runtime. Any adapter that passes conformance test can be registered.

OS Core remains: Work Queue, State Machine, Quality Gate, Audit Packet, Skill Registry.

---

## Path Compliance (updated v0.46.5)

### External Runtimes (Codex / Claude Code / OpenClaw)

- **write_forbidden_paths_default:** `private/`, `memory-system/`, `.git/`, `os-skills/`, `~/.hermes/`, `/tmp/`
- **read_restricted_paths_default:** `private/`, `memory-system/`, `os-skills/`

Unless explicitly mediated through OS handoff packet, external runtimes must NOT access these paths.

### OS Internal Workers (local_script_adapter / OS worker)

May operate `private/work-queue/` under Work Queue state machine rules:
- `private/work-queue/inbox/` — read
- `private/work-queue/outbox/` — write
- `private/work-queue/state/` — read/write audit state
- `private/work-queue/done/` — write completed tasks

This is NOT a violation of path compliance — OS workers are internal to the OS, not external runtimes.
