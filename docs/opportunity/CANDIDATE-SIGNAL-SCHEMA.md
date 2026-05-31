# Candidate Signal Schema

> **Version:** v1.0 / 2026-05-31
> **JSON Schema:** `config/schemas/candidate_signal.schema.json`

---

## 1. Candidate Types

Every candidate signal is one of:

| Type | Description | Example |
|:-----|:------------|:--------|
| `venture_opportunity` | Commercial opportunity — product, tool, content, service | "AI Seller Finance Report" |
| `os_improvement` | System improvement — OS should evolve | "Recurring workflow block needs auto-recovery Skill" |

---

## 2. Fields

### Required Fields

| Field | Type | Description |
|:------|:-----|:------------|
| `candidate_id` | string | Format: `CD-YYYYMMDD-NNN` |
| `candidate_type` | enum | `venture_opportunity` or `os_improvement` |
| `title` | string | Max 120 chars |
| `created_at` | ISO 8601 | `2026-05-31T10:00:00Z` |
| `signal_source.source_type` | enum | See Section 2.1 |
| `signal_source.source_tier` | int | 1, 2, or 3 |
| `primary_engine` | enum | See Section 2.2 |
| `related_product_lines` | string[] | Min 1, max 3 |
| `evidence_gate_status` | enum | `passed`, `needs_more_evidence`, `weak_candidate` |
| `recommended_route` | enum | See Section 2.3 |
| `status` | enum | `candidate`, `promoted`, `dismissed`, `needs_more_evidence` |

### Optional Fields

| Field | Type | Description |
|:------|:-----|:------------|
| `secondary_engines` | string[] | Including `os_evolution` |
| `signal_source.source_refs` | array | URL + excerpt or internal reference |
| `signal_type` | string | `pain`, `capability`, `trend`, `platform`, `asset`, `system_gap` |
| `company_context_refs` | string[] | Links to Company Context fields |
| `target_user` | string | Target user segment |
| `pain` | string | Pain description grounded in source evidence |
| `evidence_summary` | string | Summary of supporting evidence |
| `why_now` | string | Timing window analysis |
| `founder_fit_score` | int | 1-5 |
| `asset_leverage_score` | int | 1-5 |
| `mvp_wedge` | string | Minimum validation wedge |
| `distribution_hint` | string | Distribution channels |
| `risk` | string | Risk assessment |
| `missing_evidence` | string | What still needs validation |

### 2.1 source_type Values

```
user_complaint | ai_capability | market_trend | platform_shift
| asset_scan | os_feedback
```

### 2.2 primary_engine Values

```
cash_engine | attention_engine | platform_play
| content_engine | knowledge_asset | os_evolution
```

### 2.3 recommended_route Values

```
promote_signal | request_card | request_deep_research
| park | dismiss | create_os_improvement_task
```

---

## 3. Examples

### venture_opportunity

```yaml
candidate_id: "CD-20260531-001"
candidate_type: "venture_opportunity"
title: "Amazon sellers need automated P&L without spreadsheets"
created_at: "2026-05-31T10:00:00Z"
signal_source:
  source_type: "user_complaint"
  source_tier: 1
  source_refs:
    - url: "https://reddit.com/r/AmazonSeller/..."
      excerpt: "I spend 4 hours every month reconciling P&L..."
signal_type: "pain"
primary_engine: "cash_engine"
secondary_engines:
  - "knowledge_asset"
  - "os_evolution"
related_product_lines:
  - "ai_seller_finance"
company_context_refs:
  - "founder_fit: finance_domain_experience"
  - "asset_leverage: ai_company_os_codebase"
target_user: "Amazon sellers doing $100K-$5M/year"
pain: "Manual P&L reconciliation takes 3-5 hours per month per marketplace"
evidence_summary: "5 Reddit threads, 2 WeChat groups, 3 product reviews highlight same pain"
why_now: "Finaloop $55M raise validates willingness to pay; no Chinese-market competitor"
founder_fit_score: 5
asset_leverage_score: 4
mvp_wedge: "Single marketplace P&L report, delivered as PDF, $19/report"
distribution_hint: "WeChat seller groups + Xiaohongshu content"
risk: "Integration complexity with Amazon SP-API"
missing_evidence: "Need to validate specific price point via pre-order"
evidence_gate_status: "passed"
recommended_route: "request_card"
status: "candidate"
```

### os_improvement

```yaml
candidate_id: "CD-20260531-002"
candidate_type: "os_improvement"
title: "Workflow X85 recurring failures need auto-retry Skill"
created_at: "2026-05-31T10:00:00Z"
signal_source:
  source_type: "os_feedback"
  source_tier: 1
  source_refs:
    - type: "run_ledger_pattern"
      detail: "3 identical failures in 7 days, same step"
signal_type: "system_gap"
primary_engine: "os_evolution"
secondary_engines: []
related_product_lines:
  - "ai_company_os"
target_user: "Founder / OS Operator"
pain: "Manual recovery takes ~15min per incident"
evidence_summary: "3 failures in 7 days on step 'data_sync'"
why_now: "Failure rate increasing; manual overhead grows with workflow count"
founder_fit_score: 5
asset_leverage_score: 3
mvp_wedge: "Add configurable retry with backoff to workflow_runner.py"
distribution_hint: "N/A — internal improvement"
risk: "Auto-retry may mask underlying issues"
missing_evidence: "Verify failures are transient, not structural"
evidence_gate_status: "passed"
recommended_route: "create_os_improvement_task"
status: "candidate"
```
