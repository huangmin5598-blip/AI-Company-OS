# ADR-20260605-003 — Pluggable Agent Interface

## Status
Active

## Date
2026-06-05

## Context

AI Company OS must not be tightly coupled to any single agent framework.

Current implementations:
- **CEO Agent**: Hermes Agent (current), GPT CEO (candidate), Claude CEO (candidate)
- **Coding Runtime**: Codex CLI, Claude Code CLI (both pending trial)
- **Agent Host**: OpenClaw (declared, not verified)
- **Local Worker**: local_script_adapter (verified B1)

## Decision

AI Company OS defines two provider-agnostic interfaces:

1. **CEO Agent Interface** — task decomposition, priority, audit review, founder dialogue
2. **Runtime Adapter Interface** — accept work item, execute, write outbox, return evidence

Hermes / OpenClaw / Codex / Claude Code are replaceable implementations, not OS core.

## Consequences

- Any agent framework passing conformance test can be registered without OS core changes
- CEO Agent replacement requires ceo_agent_conformance_test, not architecture rework
- Runtime Adapter replacement requires runtime_adapter_conformance_test, not OS rework
- OS remains framework-agnostic as new frameworks emerge
