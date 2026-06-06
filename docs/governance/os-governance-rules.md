# AI Company OS Governance Rules — v0.46.5

> Last updated: 2026-06-06

## G1: P0/P1/P2 Continuity Rule

Any module entering P0 / MVP must simultaneously record:
- **P0:** what is currently verified
- **P1:** what will be expanded next
- **P2:** long-term complete form
- What is explicitly NOT done
- Trigger conditions for next phase
- Deposition location

---

## G2: Canonical Repo Path Rule

All of the following MUST execute within the canonical repo:
- Codex execution
- Claude Code execution
- GitHub release
- Public evidence updates
- README / documentation changes
- Any code or doc modifications that should appear in GitHub

Canonical repo resolution (in priority order):
1. Environment variable: `AI_COMPANY_OS_CANONICAL_REPO`
2. Local config: `private/runtime/local-paths.yaml` (gitignored)

**Public governance documents must NOT contain local absolute paths or user-specific paths.**

Actual local paths are stored in `private/runtime/local-paths.yaml` (gitignored).
Public documents describe rules, not local environment details.

---

## G3: One Active CEO Rule

Only ONE CEO Agent can be active at any time.
Hermes is current implementation, replaceable.
Replacement requires: CEO Agent Conformance Test + Founder approval.
Registry: `os-agents/registries/ceo-agent-profiles.yaml`

---

## G4: Runtime Adapter Registration Rule

New runtimes can be registered as:
- `candidate` / `declared_not_verified` (exploration stage)
- `available_not_tested` (ready for trial)

Before a runtime can:
- Execute real work through OS Work Queue, OR
- Be upgraded to `smoke_test_passed` / `verified`

It must pass Runtime Adapter Conformance Test.

---

## G5: No Direct Execution by CEO Rule

CEO Agent default: does NOT execute tasks directly.
Can create: Task Card / Handoff Packet / Review Audit Packet.
Must NOT: impersonate executor, bypass Work Queue, call coding runtime without Execution Envelope.

---

## G6: Framework-Agnostic OS Rule

AI Company OS does NOT bind to any specific runtime or framework.

| Component | Role |
|-----------|------|
| Hermes | Current CEO implementation, not OS core |
| OpenClaw | Agent host / ACP launcher, not OS Work Queue |
| Codex / Claude | Coding runtimes, not OS executors |
| Paperclip / CrewAI / Dify / LangGraph / AutoGen | Future compatible |

OS Core (NOT replaceable):
- Work Queue + State Machine
- Quality Gate
- Audit Packet
- Skill Registry
- Runtime Adapter Interface

---

## G7: OS Skill Protocol Rule

OS Skill capability must be framework-agnostic:

| Phase | Target |
|-------|--------|
| P0 | `os-skills/skill-registry.yaml` as source of truth |
| P1 | `tools/os-skill list` / `lookup` / `show` CLI for universal skill access |
| P2 | Skill Router + Context Pack Builder |

Skills are NOT Hermes-locked. Any adapter that implements skill protocol can access OS skill pool.