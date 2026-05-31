# Enrichment Review Template

> **Part of v0.34 — Signal Enrichment & Evidence Review P0**
> Defines the review workflow and template format for enriched signals that cannot pass the Evidence Gate automatically.
> When the enricher cannot determine critical fields (target_user, pain) with sufficient confidence, the signal enters `review_needed` — and the Founder (you) fills in the gaps.

---

## 1. Purpose

The **review template** is the human-in-the-loop bridge between automatic enrichment and the Evidence Gate. It serves three purposes:

1. **Surface gaps clearly** — Shows exactly which fields are `missing` or `inferred`, with the source excerpt and the enricher's reasoning.
2. **Guide the Founder** — Provides structured sections to fill in missing data, approve/reject inferred fields, or decide to dismiss the signal.
3. **Produce a machine-parsable result** — Once filled, the system updates the enriched signal's status to `reviewed`, `promoted`, or `dismissed`.

```
SourceNote
    ↓ (auto)
Enriched Signal
    ├── enrich_and_promote → Evidence Gate (no human needed)
    ├── dismiss            → Dead letter (no human needed)
    ├── request_deep_research → Needs more data
    └── review_needed      → ⭐ THIS PATH
                                ↓
                         Review Template (generated)
                                ↓ (Founder fills)
                         Reviewed Signal
                                ↓ Update
                         Enriched Signal → status=reviewed
                                ↓
                         Evidence Gate (or dismiss)
```

---

## 2. Workflow

### 2.1 When does a signal need review?

The enricher sets `review_needed` when:

| Condition | Example |
|:----------|:--------|
| `target_user` is `missing` | Source is a generic article with no user segment |
| `pain` is `missing` | Source is a trend report with no explicit pain point |
| Both `target_user` and `pain` are `inferred` with confidence < 0.6 | Weak signals that need human validation |
| Too many critical fields are `inferred` and overall confidence drops below 0.6 | Cannot safely promote without review |

### 2.2 Steps

```
1. Enricher finishes → signal.status = "enriched", recommended_next_step = "review_needed"
2. Run: python3 scripts/opportunity_enricher.py generate-review --id ES-20260531-002
   → Creates: research/opportunity-enriched/reviews/ES-20260531-002_REVIEW.md
3. Founder edits the review file, filling in blanks
4. Run: python3 scripts/opportunity_enricher.py apply-review --id ES-20260531-002
   → Reads review file, updates enriched signal:
     - status → "reviewed" (or "dismissed")
     - Founder's corrections applied to target_user/pain/why_now
     - founder_notes updated with timestamps
5. Signal is ready for Evidence Gate
```

### 2.3 The Founder's Responsibilities

When reviewing, you make **3 types of decisions**:

| Decision | What to do |
|:---------|:-----------|
| **Fill missing** | If you know the target user or pain from context, write it in. Mark as `inferred_founder` (Founder-sourced, treated as `evidence_backed`). |
| **Approve inferred** | If the enricher's `inferred` value looks correct, confirm it. |
| **Reject + replace** | If the enricher's `inferred` value is wrong, provide the correct value. |
| **Dismiss** | If the signal truly isn't relevant, dismiss it permanently. |

---

## 3. Template Format

Each review file has 5 sections. The `generate-review` command fills in what it can; the Founder fills in the **`[FOUNDER_INPUT]`** markers.

### Section A — Summary (auto-filled)

```
# Enrichment Review: ES-20260531-002

## A. Summary

| Field | Value |
|:------|:------|
| Source Note | SN-search_query-20260531-001 — "Agent OS trends" |
| Source URL | https://example.com/article |
| Current Status | enriched |
| Recommended Action | review_needed |
| Overall Confidence | 0.17 / 1.0 |
| Generated | 2026-05-31T06:00:00Z |
```

### Section B — Field-by-Field Review (auto-filled, Founder fills blanks)

```
## B. Target User

**Current Value:** (empty)
**Evidence Status:** missing
**Enricher's Note:** No user segment pattern found in excerpt, title, or refs

### Founder Decision

- [ ] **Fill in**: [FOUNDER_INPUT: Who is the target user?]
- [ ] **Dismiss**: This signal has no clear user → dismiss

If filled, evidence status: `inferred_founder`
```

Repeat for pain and why_now.

### Section C — Overall Decision (Founder fills)

```
## C. Decision

- [ ] **Promote to Evidence Gate** — All critical fields filled or confirmed
- [ ] **Request deep research** — Signal is promising but needs more data
- [ ] **Dismiss** — Not relevant to current product direction
```

### Section D — Founder Notes (Founder fills, optional)

```
## D. Founder Notes

- [FOUNDER_NOTE: Your reasoning or observations]
```

### Section E — Review Metadata (auto-filled on apply)

```
## E. Review Metadata

| Field | Value |
|:------|:------|
| Reviewed By | [FOUNDER_INPUT: Your name or initials] |
| Review Date | [auto-filled on apply] |
```

---

## 4. Key Rules

1. **Founder fills are `inferred_founder`** — They get a new evidence_status value that means "Founder validated". This is treated as equivalent to `evidence_backed` for the Evidence Gate.
2. **Founder can dismiss any signal** — Even if it could be enriched, if it doesn't feel right, dismiss it.
3. **No partial promotions** — A signal only goes to the Evidence Gate after all critical fields are resolved.
4. **Review files are Layer 2 data** — Never committed to GitHub. Go in `research/opportunity-enriched/reviews/` (already under `.gitignore` via parent dir).
5. **Re-review is possible** — Running `generate-review` again overwrites the review file. Running `apply-review` again reads the current state.

---

## 5. When to Skip Review

Not every `review_needed` signal needs a human. Skip review when:

- **Both target_user and pain are `missing`** and the source is clearly noise → just run `dismiss`
- **The signal is clearly a `request_deep_research` case** → run the deep research connector, don't fill in guesses

Example:
```bash
# Skip review, dismiss directly
python3 scripts/opportunity_enricher.py dismiss --id ES-20260531-002

# Skip review, request research
python3 scripts/opportunity_enricher.py request-research --id ES-20260531-002
```

---

## 6. Example Filled Review

```markdown
# Enrichment Review: ES-20260531-002

## B. Target User

**Current Value:** (empty)
**Evidence Status:** missing
**Enricher's Note:** No user segment pattern found in excerpt

### Founder Decision

- [x] **Fill in**: AI-native founders building multi-agent systems
- [ ] **Dismiss**: This signal has no clear user → dismiss
```

After `apply-review`, the enriched signal is updated:
```json
{
  "target_user": {
    "value": "AI-native founders building multi-agent systems",
    "evidence_status": "inferred_founder",
    "evidence": "Founder review: inferred from product line context (ai_company_os)"
  },
  "founder_notes": [
    {
      "timestamp": "2026-05-31T07:00:00Z",
      "action": "reviewed",
      "note": "Filled missing target_user from context. Signal is relevant to Agent OS product line."
    }
  ],
  "status": "reviewed"
}
```

---

## 7. Automation Boundaries

| What | Auto | Manual |
|:-----|:----:|:------:|
| Detect `review_needed` | ✅ enricher | — |
| Generate review template | ✅ `generate-review` | — |
| Fill missing fields | — | ✅ Founder |
| Approve/reject inferred | — | ✅ Founder |
| Dismiss signal | ✅ (both missing) | ✅ (any time) |
| Apply review back | ✅ `apply-review` | — |
| Send to Evidence Gate | ✅ `apply-review` | — |
