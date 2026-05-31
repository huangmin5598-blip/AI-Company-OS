# SourceNote Contract

> **Part of v0.33 — Opportunity Signal Source Layer P0**
> Defines the unified input format for all external signal connectors.
> Every connector must output SourceNote. Every SourceNote must conform to this contract.

---

## 1. Purpose

The SourceNote Contract is the **unified data interface** between signal connectors and the opportunity discovery engine.

```text
Connectors (Search/GitHub/RSS/...)
    ↓ fetch → parse
SourceNote (this contract)
    ↓ to_source_note()
opportunity_scout.py scan --source-file <source_note>
    ↓ evidence gate + scoring
Candidate Signal (CD-YYYYMMDD-NNN)
```

**Key principle:** Connectors never generate candidates. They produce SourceNotes. The scout engine (v0.32) handles all judging, scoring, and routing.

---

## 2. SourceNote Fields

### 2.1 Required Fields

| Field | Type | Description |
|:------|:-----|:------------|
| `source_note_id` | string | Unique ID per connector run. Format: `SN-{connector_id}-{YYYYMMDD}-{NNN}` |
| `connector_id` | string | Which connector produced this. e.g. `search_query`, `github` |
| `source_platform` | string | Where the content originated. e.g. `reddit`, `github`, `g2`, `product_hunt`, `rss`, `web` |
| `source_category` | enum | Signal category. One of: `user_complaint`, `ai_capability`, `market_trend`, `platform_shift`, `asset_scan`, `os_feedback` |
| `source_tier` | int | Data quality tier. `1` = primary evidence, `2` = secondary, `3` = weak/contextual |
| `title` | string | Short descriptive title. Max 120 chars |
| `url` | string | Source URL. Must be a valid HTTP/HTTPS URL |
| `excerpt` | string | Short excerpt of the source content. **Never full content.** Max 500 chars |
| `fetched_at` | string | ISO 8601 timestamp when the connector fetched the data |
| `dedupe_key` | string | Unique key for deduplication. Format: `{source_platform}:{url_sha256_prefix}` or `{connector_id}:{internal_id}` |

### 2.2 Optional Fields

| Field | Type | Description |
|:------|:-----|:------------|
| `query_or_feed` | string | The query or feed URL that produced this SourceNote |
| `published_at` | string | ISO 8601 timestamp of original publication (if available) |
| `source_ref` | string | Reference for traceability. Can be a path, ID, or additional URL |
| `watchlist_refs` | array | Links to watchlist domains (e.g. `amazon_seller_finance`) |
| `product_line_refs` | array | Suggested product lines (scout engine may override) |
| `raw_signal_type` | string | Connector's best guess at signal type. Scout engine will reclassify |
| `confidence` | float | Connector's confidence in this signal. 0.0–1.0 |
| `metadata` | object | Connector-specific metadata. Must be JSON-serializable |

### 2.3 source_category Values

```text
user_complaint  — Direct user pain point from forums, reviews, complaints
ai_capability   — New AI models, APIs, frameworks, capabilities
market_trend    — Funding news, policy changes, industry shifts
platform_shift  — Platform ecosystem changes (Shopify API, Roblox, etc.)
asset_scan      — Internal assets found (code, docs, methodologies)
os_feedback     — OS runtime feedback (failures, blocks, patterns)
```

### 2.4 source_tier Rules

| Tier | Meaning | Example |
|:-----|:--------|:--------|
| `1` | Primary evidence. Direct user quote, verified post, official announcement | User complaint with URL and excerpt |
| `2` | Secondary evidence. Summary, analysis, or indirect reference | News article about a trend |
| `3` | Weak/contextual. Might be relevant but needs more evidence | Generic discussion, low-confidence signal |

---

## 3. Connector Interface

Every connector must implement:

```python
class BaseConnector:
    def fetch(self) -> list[dict]:
        """Fetch raw data from the source."""
        pass

    def parse(self, raw_data: list[dict]) -> list[dict]:
        """Parse raw data into structured SourceNote dicts."""
        pass

    def to_source_note(self, parsed: dict) -> dict:
        """Convert a single parsed item into a valid SourceNote dict."""
        pass

    def dedupe_key(self, source_note: dict) -> str:
        """Return a unique deduplication key for this source note."""
        pass

    def run(self) -> list[dict]:
        """Full pipeline: fetch → parse → to_source_note for all items."""
        raw = self.fetch()
        parsed = self.parse(raw)
        return [self.to_source_note(p) for p in parsed]
```

### 3.1 Contract Rules

1. **Connectors do NOT generate candidates.** The scout engine does that.
2. **Connectors do NOT save full content.** Only excerpt (max 500 chars).
3. **Connectors must set fetch timestamp** (`fetched_at`) on every SourceNote.
4. **Connectors must set a unique dedupe_key** for idempotent re-runs.
5. **Errors in one item must not block the batch.** Log the error, skip the item, continue.

---

## 4. Deduplication Strategy

Each SourceNote has a `dedupe_key`. Duplicate detection is:

1. **Within a single run:** Same `dedupe_key` in one batch → first wins, rest skipped.
2. **Across runs:** Same `dedupe_key` already exists in `research/opportunity-source-notes/` → skip.
3. **Cross-connector:** Different connectors may produce SourceNotes from the same source. This is intentional — the scout engine handles evaluation.

---

## 5. Output Location

SourceNotes are written as individual JSON files to:

```text
research/opportunity-source-notes/{connector_id}/{source_note_id}.json
```

This directory is in `.gitignore` (Layer 2 — instance data).

---

## 6. JSON Schema

The formal JSON Schema is at `config/schemas/source_note.schema.json`.

Validate any SourceNote with:

```bash
python3 -c "
import json, jsonschema
with open('config/schemas/source_note.schema.json') as f:
    schema = json.load(f)
with open('research/opportunity-source-notes/search_query/SN-xxx.json') as f:
    note = json.load(f)
jsonschema.validate(instance=note, schema=schema)
print('✅ Valid')
"
```

---

## 7. Example SourceNote

```json
{
  "source_note_id": "SN-search_query-20260531-001",
  "connector_id": "search_query",
  "source_platform": "reddit",
  "source_category": "user_complaint",
  "source_tier": 1,
  "query_or_feed": "amazon seller profit report problem",
  "title": "Amazon seller struggling with manual P&L reconciliation",
  "url": "https://reddit.com/r/AmazonSeller/comments/abc123/",
  "published_at": "2026-05-30T14:22:00Z",
  "fetched_at": "2026-05-31T06:00:00Z",
  "excerpt": "\"I spend 4 hours every month manually pulling P&L data from Amazon. There has to be a better way.\"",
  "source_ref": "reddit:abc123",
  "watchlist_refs": ["amazon_seller_finance"],
  "product_line_refs": ["ai_seller_finance"],
  "raw_signal_type": "user_complaint",
  "confidence": 0.85,
  "dedupe_key": "reddit:abc123"
}
```

---

## 8. Data Boundaries

- **SourceNotes are Layer 2 data** (instance data). Never committed to GitHub.
- **Connector code is Layer 3** (reusable framework). Goes in `scripts/connectors/`.
- **Config files** follow the existing pattern: `*.example.yaml` in git, real files in `.gitignore`.
- **Quality reports** go to `research/opportunity-source-layer/` (Layer 2, not committed).
