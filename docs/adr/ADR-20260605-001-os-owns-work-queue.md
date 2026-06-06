# ADR-20260605-001 — OS Owns the Work Queue

**Status:** Accepted
**Date:** 2026-06-05
**Type:** Architecture Decision Record

---

## Decision

AI Company OS owns Work Queue, State Machine, Quality Gate, Audit Packet, Skill Registry.
External agent frameworks are Runtime Adapters, not the OS control plane.

---

## Reason

1. OpenClaw does not natively provide inbox scanning, Execution Envelope parsing, or external task queue API
2. TaskFlow is internal orchestration, not external queue
3. OpenClaw CLI / agentTurn is conversation-oriented, not reliable as silent executor
4. CLI direct call: session_id returns, silent file write fails, agent tends to dialogue

---

## Implication

- **Hermes** = CEO / Dispatcher / Reviewer / Strategy Interface
- **OpenClaw** = Runtime Adapter / ACP Host / Agent Container
- **Codex / Claude Code** = Coding Runtime Adapters
- **Local Script** = Deterministic Runtime Adapter
- **Paperclip** = Future Runtime Adapter candidate

---

## Work Queue Owner

AI Company OS must have its own Work Queue with:
- State Machine: inbox → claimed → running → waiting_review → done / failed
- Lock mechanism: attempt_id, worker_id, lease_expires_at, heartbeat_at
- Audit Evidence: artifact_hashes, queue_state_transitions, written_by

---

## Runtime Adapter Contract

All external agent frameworks must implement Runtime Adapter Contract:
- adapter_id
- invocation_method
- supports_parallel
- supports_file_write
- returns_session_id
- verification_status (declared | verified | partially_verified | failed | blocked)
- limitations (honest disclosure)

---

## Reviewed By

- Founder (2026-06-05)
- Hermes Agent
- GPT Process Enforcer
