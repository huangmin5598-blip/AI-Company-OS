# 📊 Evidence Dashboard Lite

**Version**: 1.0 (External Preview)
**Purpose**: Public evidence layer for GitHub / independent site / social media sharing

---

## What This Shows

This dashboard provides a transparent view of the AI Company OS in operation. It answers the question: **"Is the system actually running?"**

The answer is visible in 5 clear modules:

| # | Module | What It Shows |
|---|--------|----------------|
| 1 | **Project Board** | Current projects and their status |
| 2 | **Agent Status** | How many agents are running and their roles |
| 3 | **Run Flow** | How tasks flow through the system |
| 4 | **Asset Growth** | What the system has produced and accumulated |
| 5 | **Gateway Summary** | Cost and governance in action |

---

## Quick Summary

- ✅ **System is running** — 14 agents active
- ✅ **Projects are progressing** — 7 projects, 6 active
- ✅ **Agents are collaborating** — multi-agent workflows in place
- ✅ **Assets are growing** — 50+ novels, 1000+ documents
- ✅ **Governance is working** — cost tracking, fallback mechanisms

---

## Module Details

### 1. Project Board
Shows all projects currently in the system.

| Project | Lead | Stage | Status |
|---------|------|-------|--------|
| novel-v1 | lead-novel | ITERATION | ACTIVE |
| research-agent | research-agent | ACTIVE | ACTIVE |
| control-center-v1 | tiger-coder | P0 | ACTIVE |
| capability-registry-v1 | tiger-coder | P0 | ACTIVE |
| gateway-lite-v1 | tiger-coder | MVP | ACTIVE |

📄 [View Project Board](./project-board-external.md)

---

### 2. Agent Status
Shows all AI agents and their current status.

**Total**: 14 agents
- **Working**: 1 (tiger-coder)
- **Idle**: 13

| Agent | Role | Status |
|-------|------|--------|
| main | CEO Assistant | idle |
| lead-novel | Project Lead | idle |
| story-editor | Structure Design | idle |
| writer | Content Production | idle |
| review-editor | Quality Control | idle |
| research-agent | Opportunity Research | idle |
| tiger-coder | System Development | working |

📄 [View Agent Status](./agent-status-external.md)

---

### 3. Run Flow
Shows how tasks move through the system.

**novel-v1 Workflow**:
```
lead-novel → story-editor → writer → review-editor → PASS
```

- Daily output: 2 short novels
- Success rate: 80% (straight-through)
- Revision rate: 15%
- Escalation rate: 5%

📄 [View Run Flow](./run-flow-external.md)

---

### 4. Asset Growth
Shows accumulated assets over time.

| Asset Type | Count | Trend |
|------------|-------|-------|
| Novels | 50+ | +2/day |
| Documents (MD) | 1059 | Growing |
| Code Files | 90+ | Growing |
| Knowledge Cards | 20+ | Weekly update |

📄 [View Asset Growth](./asset-growth-external.md)

---

### 5. Gateway Summary
Shows cost and governance data.

| Metric | Value |
|--------|-------|
| Daily Calls | 8 |
| Daily Cost | $0.00255 |
| Fallback | 2 (timeout → local model) |
| Success Rate | 100% |

📄 [View Gateway Summary](./gateway-summary-external.md)

---

## For Screenshot / Recording

These files are formatted for easy capture:

- Clean table layouts
- Clear section headers
- Emoji indicators for status
- No internal jargon

**Best for**:
- GitHub repository showcase
- Independent site "Status" page
- Social media documentation
- Demo videos

---

## Data Sources

All data comes from real system execution:

- `TASK-POOL.md` — Project registry
- `CAPABILITY-REGISTRY.md` — Agent capabilities
- `openclaw agents list` — Agent runtime state
- `gateway-lite/daily/*.json` — Cost records
- `novel-v1/manuscripts/` — Content output
- `novel-v1/TASK-CARDS/` — Task records

---

## Update Frequency

This dashboard is refreshed manually for now.

**Next step**: Scheduled updates (daily/weekly) as the system matures.

---

*Last updated: 2026-04-01 (Asia/Shanghai)*