# OpenClaw Data Source Scan Report

> **Project**: AI Company Control Center v0.1
> **Scan Date**: 2026-05-17
> **Scanner**: Hermes Agent
> **Status**: ✅ All key data sources verified

---

## Summary

| # | Data Source | Path | Format | Status | Records | Parse Strategy |
|:-:|-------------|------|:------:|:------:|:-------:|:--------------:|
| 1 | Agent List | `openclaw agents list` CLI | Text | ✅ Found | 17 agents | CLI → text parse |
| 2 | Cron Jobs | `~/.openclaw/cron/jobs.json` | JSON | ✅ Found | 20+ jobs | `json.load` |
| 3 | Production Ledger | `run-ledger-v1/db/production-flow-ledger.json` | JSON | ✅ Found | ~15 runs | `json.load` |
| 4 | Artifact Ledger | `run-ledger-v1/db/artifact-ledger.json` | JSON | ✅ Found | ~10 artifacts | `json.load` |
| 5 | Cost by Model | `workspace-gateway-lite/cost-view/by-model.json` | JSON | ✅ Found | 2 models | `json.load` |
| 6 | Cost by Agent | `workspace-gateway-lite/cost-view/by-agent.json` | JSON | ✅ Found | 6 agents | `json.load` |
| 7 | Cost by Project | `workspace-gateway-lite/cost-view/by-project.json` | JSON | ✅ Found | 3 projects | `json.load` |
| 8 | Daily Cost | `workspace-gateway-lite/daily/2026-03-30.json` | JSON | ✅ Found | 6 entries | `json.load` |
| 9 | Subagent Runs | `~/.openclaw/subagents/runs.json` | JSON | ✅ Found | 50+ runs | `json.load` |
| 10 | YAML Production Ledger | `novel-v1/registry/production-ledger.yaml` | YAML | ✅ Found | 10+ records | `yaml.safe_load` |
| 11 | Business Line Registry | `BUSINESS-LINE-REGISTRY.md` | Markdown | ✅ Found | 5 lines | Manual (mock) |
| 12 | Run Ledger (in-memory) | `projects/run-ledger-v1/db/ledger.js` | JS array | ⚠️ Exists | In-memory only | Not parseable |

---

## 1. Agent List

**Path**: `openclaw agents list` CLI
**Format**: Text (CLI output)
**Status**: ✅ Available

**Sample Output**:
```
Agents:
- main (default)
  Workspace: ~/.openclaw/workspace
  Agent dir: ~/.openclaw/agents/main/agent
  Model: minimax-cn/MiniMax-M2.5
  Routing rules: 0
- tiger-coder
  Identity: 😎 Tiger-编程专家 (config)
  Workspace: ~/.openclaw/workspace-tiger-coder
  Model: minimax-cn/MiniMax-M2.5
  Routing rules: 1
```

**Total Agents**: 17
**Parse Strategy**: Run CLI, parse lines with regex for agent name, identity, workspace, model, routing_rules
**Fallback**: If CLI unavailable, use last cached data from SQLite

**Known Agents**:
main, tiger-coder, amazon-seller, content-manager, finance-analyst, course-builder,
lead-hub, lead-sticker, research-agent, lead-novel, lead-motionclean,
story-editor, writer, review-editor, lead-os, demand-miner, creative-lab

---

## 2. Cron Jobs

**Path**: `~/.openclaw/cron/jobs.json`
**Format**: JSON
**Status**: ✅ Found

**Sample Record**:
```json
{
  "id": "e2dbc742-...",
  "agentId": "main",
  "name": "亚马逊选品报告",
  "enabled": false,
  "schedule": { "expr": "0 9 * * 2,4", "kind": "cron", "tz": "Asia/Shanghai" },
  "state": {
    "lastRunAtMs": 1771462800008,
    "lastStatus": "error",
    "lastDurationMs": 152200,
    "consecutiveErrors": 1,
    "lastError": "cron announce delivery failed"
  }
}
```

**Total Jobs**: 20+ across 5 business lines
**Parse Strategy**: `json.load` → iterate jobs array
**Fallback**: Return empty array if file missing

---

## 3. Production Ledger

**Path**: `~/.openclaw/workspace/run-ledger-v1/db/production-flow-ledger.json`
**Format**: JSON
**Status**: ✅ Found

**Sample**:
```json
{
  "runs": [{
    "runIntentId": "test-flow-001",
    "artifactId": "artifact-mo2wmgds-5dvq",
    "validatorPassed": true,
    "updatedAt": "2026-04-17T12:48:33.906Z"
  }]
}
```

**Alternate Source**: `novel-v1/registry/production-ledger.yaml` (YAML, more detailed)

**YAML Sample**:
```yaml
- record_id: record-novel-111-01
  task_id: guarantee-2026-04-26
  project_id: novel-v1
  date: 2026-04-26
  final_output_path: manuscripts/2026-04-26/chapter-novel-111-2026-04-26.md
  word_count: 6145
  result: passed
```

**Parse Strategy**: `json.load` for JSON; `yaml.safe_load` for fallback YAML
**Fallback**: Return empty array

---

## 4. Artifact Ledger

**Path**: `~/.openclaw/workspace/run-ledger-v1/db/artifact-ledger.json`
**Format**: JSON
**Status**: ✅ Found

Contains artifact records with run IDs and validation status.

---

## 5-7. Cost Views (Model / Agent / Project)

**Path**: `~/.openclaw/workspace-gateway-lite/cost-view/{by-model,by-agent,by-project}.json`
**Format**: JSON
**Status**: ✅ All three files found

**by-model.json Sample**:
```json
{
  "MiniMax-M2.5": {
    "total_calls": 6,
    "total_cost_usd": 0.00255,
    "agents": ["story-editor", "research-agent", "lead-novel", "finance-analyst", "writer", "review-editor"],
    "is_local": false,
    "cost_per_call": 6.7e-05
  }
}
```

**by-agent.json Sample**:
```json
{
  "finance-analyst": {
    "total_calls": 1,
    "total_cost_usd": 0.00038,
    "input_tokens": 80,
    "output_tokens": 150
  }
}
```

**Parse Strategy**: `json.load`, aggregate by key
**Fallback**: Return empty dict

---

## 8. Daily Cost Details

**Path**: `~/.openclaw/workspace-gateway-lite/daily/2026-03-30.json`
**Format**: JSON
**Status**: ✅ Found (sample date)

**Sample**:
```json
{
  "date": "2026-03-30",
  "entries": [
    {
      "timestamp": "2026-03-30T19:05:48+08:00",
      "agent_id": "finance-analyst",
      "provider": "minimax-cn",
      "model": "MiniMax-M2.5",
      "input_tokens": 80,
      "output_tokens": 150,
      "estimated_cost_usd": 0.00038,
      "result_status": "success",
      "fallback_triggered": false
    }
  ]
}
```

**Parse Strategy**: `json.load` entries array
**Fallback**: Return empty array

---

## 9. Subagent Runs

**Path**: `~/.openclaw/subagents/runs.json`
**Format**: JSON (version 2 format)
**Status**: ✅ Found

Contains full subagent spawn history with: runId, childSessionKey, controllerSessionKey, task content (base64), workspaceDir, model, outcome status, timestamps.

**Parse Strategy**: `json.load` → access `runs` dict
**Fallback**: Return empty dict

---

## 10. YAML Production Ledger (Alternate)

**Path**: `~/.openclaw/workspace/novel-v1/registry/production-ledger.yaml`
**Format**: YAML
**Status**: ✅ Found

Contains detailed per-chapter execution records spanning April 2026 (chapter 35-111).

**Parse Strategy**: `yaml.safe_load` → list of record objects
**Fallback**: Only use if JSON production-ledger is incomplete

---

## 11. Business Line Registry (Manual)

**Path**: `BUSINESS-LINE-REGISTRY.md`
**Format**: Markdown
**Status**: ✅ Found but parsed manually for v0.1

Known business lines:
- novel-v1 (Guaranteed): Novel daily production
- content-manager (Running): Content operations
- finance-analyst (Running): Financial analysis
- amazon-seller (Error): Amazon product selection
- research-opportunity (Scaffolded): Research

**Strategy**: v0.1 uses hardcoded business lines in seed data. Future versions should write a structured registry.

---

## 12. Run Ledger (In-memory)

**Path**: `projects/run-ledger-v1/db/ledger.js`
**Format**: JavaScript (in-memory array)
**Status**: ⚠️ Not directly parseable

The Run Ledger stores events in a JS array in memory. No persistent file output for the event stream.
**Workaround**: Use production-flow-ledger.json + artifact-ledger.json as the primary execution data source.

---

## Data Source Health Summary

| Status | Count | Data Sources |
|:------:|:-----:|-------------|
| ✅ Directly readable | 9 | Cron Jobs, Cost views (3), Daily cost, Subagent runs, Production ledger, Artifact ledger, YAML ledger |
| ⚠️ Needs CLI call | 1 | Agent list (openclaw agents list) |
| ⚠️ Manual/Mocked | 2 | Business Line Registry, Escalation logs |
| ❌ Not parseable | 1 | Run Ledger (in-memory) |

---

## Recommendations for v0.1

1. **Primary data sources**: Cron Jobs JSON + Production Ledger JSON + Cost Views JSON
2. **Agent data**: CLI call on each refresh, cache in SQLite
3. **Business lines**: Hardcode 5 known lines in seed, expand later
4. **Escalation alerts**: Derive from cron jobs lastStatus=error
5. **Do NOT parse**: Run Ledger JS file (in-memory, no persistent output)
