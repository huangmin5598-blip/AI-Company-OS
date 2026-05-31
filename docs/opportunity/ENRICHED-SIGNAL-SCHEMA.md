# Enriched Signal Schema

> **Part of v0.34 — Signal Enrichment & Evidence Review P0**
> Defines the enriched signal format: raw SourceNote + extracted/inferred analytical fields with evidence status.
> Every field that requires judgment must declare whether it is backed by evidence, inferred, or missing.

---

## 1. Purpose

The Enriched Signal sits between a raw `SourceNote` and a `Candidate Signal`:

```text
SourceNote (raw)
    ↓
Opportunity Enricher (extract / infer / tag evidence status)
    ↓
Enriched Signal (this schema)
    ↓
Evidence Gate (checks target_user.status, pain.status, etc.)
    ↓
Candidate Signal (CD-YYYYMMDD-NNN) or review_needed
```

**Key principle:** Enrichment does NOT lower the Evidence Gate. It makes the evidence status transparent so the Gate can make better decisions.

---

## 2. Core Design

### 2.1 Evidence Status

Every analytical field in the enriched signal carries an `evidence_status`:

| Status | Meaning | Can be promoted? |
|:-------|:--------|:-----------------|
| `evidence_backed` | Directly supported by SourceNote excerpt or URL | Yes, strong signal |
| `inferred` | Reasonable deduction from evidence, but not explicitly stated | Yes, but with lower confidence |
| `missing` | No basis in the source data to determine this field | No — goes to review_needed |

### 2.2 Hard Rules

1. **No field with status `missing` can be treated as `evidence_backed`.**
2. **No LLM hallucination** — never invent users, pain points, willingness to pay, or market size from general knowledge.
3. **Evidence citations must be traceable** — each `evidence` string must point to a specific excerpt or field in the source SourceNote.
4. **`requires_founder_review` must be set to `true`** if any critical field (`target_user` or `pain`) has status `missing` or `inferred` and the overall confidence is below 0.6.
5. **Enriched signals do NOT bypass the Evidence Gate.** The Gate evaluates each field independently.

---

## 3. Fields

### 3.1 Required Fields

| Field | Type | Description |
|:------|:-----|:------------|
| `enriched_signal_id` | string | Unique ID. Format: `ES-{YYYYMMDD}-{NNN}` |
| `source_note_id` | string | Reference to the original SourceNote |
| `created_at` | string | ISO 8601 |
| `target_user` | object | See Section 3.3 |
| `pain` | object | See Section 3.3 |
| `why_now` | object | See Section 3.3 |
| `signal_type` | object | See Section 3.3 |
| `confidence` | float | Overall confidence. 0.0–1.0 |
| `requires_founder_review` | bool | `true` if any critical field is `missing` or confidence < 0.6 |
| `recommended_next_step` | enum | `enrich_and_promote`, `review_needed`, `request_deep_research`, `dismiss` |
| `status` | enum | `draft`, `enriched`, `reviewed`, `promoted`, `dismissed` |

### 3.2 Analytical Field Structure

Every analytical field uses the same structure:

```json
{
  "value": "extracted or inferred content",
  "evidence_status": "evidence_backed | inferred | missing",
  "evidence": "How this was determined. For evidence_backed: quote from source. For inferred: reasoning chain."
}
```

### 3.3 Field Definitions

#### target_user

The user segment that would benefit from this signal.

```json
{
  "target_user": {
    "value": "Amazon sellers doing $100K-$5M/year",
    "evidence_status": "evidence_backed",
    "evidence": "SourceNote excerpt: 'I spend 4 hours every month manually reconciling...'"
  }
}
```

#### pain

The specific problem or pain point.

```json
{
  "pain": {
    "value": "Manual P&L reconciliation takes 4+ hours per month",
    "evidence_status": "evidence_backed",
    "evidence": "SourceNote excerpt: 'I spend 4 hours every month manually reconciling...'"
  }
}
```

#### why_now

The timing window — why this opportunity matters now.

```json
{
  "why_now": {
    "value": "Finaloop $55M raise validates market; no Chinese-market competitor",
    "evidence_status": "inferred",
    "evidence": "SourceNote mentions competitor funding; no direct timing signal in excerpt"
  }
}
```

#### signal_type

Classification of the signal. Values match the scout engine's 6 types.

```json
{
  "signal_type": {
    "value": "pain",
    "evidence_status": "evidence_backed",
    "evidence": "SourceNote.source_category = user_complaint"
  }
}
```

Valid values: `pain`, `capability`, `trend`, `platform`, `asset`, `system_gap`

### 3.4 Optional Fields

| Field | Type | Description |
|:------|:-----|:------------|
| `source_note_ref` | string | Full reference back to the SourceNote |
| `engine_hints` | array | Suggested opportunity engines (e.g. `cash_engine`) |
| `engine_hints_status` | enum | `evidence_backed`, `inferred`, `missing` |
| `product_line_hints` | array | Suggested product lines |
| `product_line_hints_status` | enum | `evidence_backed`, `inferred`, `missing` |
| `evidence_summary` | string | Summary of all supporting evidence |
| `evidence_gaps` | array | What evidence is still missing |
| `founder_notes` | array | Historical founder notes (appended over time) |

### 3.5 recommended_next_step Values

| Value | When | Description |
|:------|:-----|:------------|
| `enrich_and_promote` | All critical fields have status `evidence_backed` or `inferred`, confidence >= 0.6 | Ready for Evidence Gate |
| `review_needed` | Any critical field is `missing`, or confidence < 0.6 | Needs founder review |
| `request_deep_research` | Evidence is too weak to make any judgment | Needs more data |
| `dismiss` | Signal is clearly not relevant | Discard |

### 3.6 status Values

| Value | Description |
|:------|:------------|
| `draft` | Enriched but not yet reviewed |
| `enriched` | Automatically enriched, no founder intervention yet |
| `reviewed` | Founder has reviewed and approved the enrichment |
| `promoted` | Sent to Evidence Gate and passed |
| `dismissed` | Sent to Evidence Gate and failed, or founder dismissed |

---

## 4. Example

```json
{
  "enriched_signal_id": "ES-20260531-001",
  "source_note_id": "SN-search_query-20260531-001",
  "created_at": "2026-05-31T06:00:00Z",
  "target_user": {
    "value": "Amazon sellers doing $100K-$5M/year",
    "evidence_status": "evidence_backed",
    "evidence": "SourceNote excerpt: 'I spend 4 hours every month manually reconciling my Amazon P&L...'"
  },
  "pain": {
    "value": "Manual P&L reconciliation takes 4+ hours per month",
    "evidence_status": "evidence_backed",
    "evidence": "SourceNote excerpt: 'I spend 4 hours every month...'"
  },
  "why_now": {
    "value": "Finaloop $55M raise validates willingness to pay; no affordable alternative for small sellers",
    "evidence_status": "inferred",
    "evidence": "SourceNote mentions competitor landscape; timing inferred from market activity"
  },
  "signal_type": {
    "value": "pain",
    "evidence_status": "evidence_backed",
    "evidence": "SourceNote.source_category = user_complaint"
  },
  "engine_hints": ["cash_engine", "knowledge_asset"],
  "engine_hints_status": "inferred",
  "product_line_hints": ["ai_seller_finance"],
  "product_line_hints_status": "evidence_backed",
  "evidence_summary": "Direct user complaint about manual P&L reconciliation. Reddit post with detailed pain description.",
  "evidence_gaps": [
    "No explicit willingness to pay",
    "No competitor pricing information"
  ],
  "confidence": 0.75,
  "requires_founder_review": false,
  "recommended_next_step": "enrich_and_promote",
  "status": "enriched"
}
```

---

## 5. Data Boundaries

- **Enriched signals are Layer 2 data** — never committed to GitHub.
- **Enrichment code is Layer 3** — goes in `scripts/opportunity_enricher.py`.
- **Enrichment configs follow the established pattern**: examples in git, real configs in `.gitignore`.
- **Enrichment events should be recorded in Run Ledger** (when available): `enriched_signal_created`, `enriched_signal_reviewed`, `enriched_signal_promoted`, `enriched_signal_dismissed`.
