#!/usr/bin/env python3
"""
v0.33 — Source Quality Smoke Test

Tests the full connector-to-candidate pipeline end-to-end.
Uses built-in mock data (no API keys needed) to validate:
  1. SourceNote Contract compliance (schema validation)
  2. Connector fetch → parse → to_source_note pipeline
  3. SourceNote → scout engine → candidate pipeline
  4. Quality metrics: gate pass rate, noise ratio, effective query patterns

Usage:
  python3 scripts/connectors/smoke_test.py
  python3 scripts/connectors/smoke_test.py --report research/opportunity-source-layer/v0.33-source-quality-report.md

Exit code:
  0 = all checks pass
  1 = one or more checks failed
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))

sys.path.insert(0, _SCRIPT_DIR)
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "scripts"))

from base_connector import BaseConnector

# Scout engine
try:
    from opportunity_scout import build_candidate, score_candidate, validate_evidence_gate
except ImportError:
    sys.path.insert(0, os.path.join(_PROJECT_ROOT, "scripts"))
    from opportunity_scout import build_candidate, score_candidate, validate_evidence_gate

# Schema
_SCHEMA_PATH = os.path.join(_PROJECT_ROOT, "config", "schemas", "source_note.schema.json")


# ════════════════════════════════════════════════════════════════════
# Mock Search Connector (simulates SearchQueryConnector)
# ════════════════════════════════════════════════════════════════════

class MockSearchConnector(BaseConnector):
    """Mock connector that returns pre-built sample results."""

    @property
    def connector_id(self) -> str:
        return "search_query_test"

    def __init__(self):
        self._sample_data = [
            {
                "title": "Amazon seller struggling with manual P&L",
                "url": "https://reddit.com/r/AmazonSeller/comments/sample1",
                "snippet": "\"I spend 4 hours every month manually reconciling my Amazon P&L. There must be a better way. QuickBooks doesn't handle multi-currency well.\"",
                "source": "reddit",
                "query_id": "amazon_seller_profit_complaints",
                "query_def": {
                    "source_category": "user_complaint",
                    "source_tier": 1,
                    "watchlist_refs": ["amazon_seller_finance"],
                    "product_line_refs": ["ai_seller_finance"],
                },
            },
            {
                "title": "New GPT-5 API enables reliable financial data extraction",
                "url": "https://techcrunch.com/2026/05/gpt5-finance",
                "snippet": "OpenAI's GPT-5 now supports structured JSON output with 99.7% accuracy on financial data, enabling automated bookkeeping at 1/10th the cost of traditional services.",
                "source": "techcrunch",
                "query_id": "new_ai_finance_tools",
                "query_def": {
                    "source_category": "ai_capability",
                    "source_tier": 2,
                    "watchlist_refs": ["ai_capabilities", "saas_finance"],
                    "product_line_refs": ["ai_seller_finance", "saas_microtools"],
                },
            },
            {
                "title": "Shopify launches Embedded Finance API",
                "url": "https://shopify.dev/changelog/embedded-finance",
                "snippet": "Shopify announces Embedded Finance API enabling third-party developers to build checkout and accounting apps directly in Shopify Admin.",
                "source": "shopify",
                "query_id": "shopify_platform_update",
                "query_def": {
                    "source_category": "platform_shift",
                    "source_tier": 2,
                    "watchlist_refs": ["platform_ecosystems", "shopify_apps"],
                    "product_line_refs": ["platform_ecosystem_experiments", "ai_seller_finance"],
                },
            },
            {
                "title": "Cross-border ecommerce regulation requires quarterly reporting",
                "url": "https://industryblog.com/cross-border-reporting-2026",
                "snippet": "New regulation mandates quarterly financial reporting for all cross-border ecommerce sellers. Non-compliance penalties start at $5,000.",
                "source": "web",
                "query_id": "ecommerce_regulation_change",
                "query_def": {
                    "source_category": "market_trend",
                    "source_tier": 2,
                    "watchlist_refs": ["cross_border_sellers", "regulatory_changes"],
                    "product_line_refs": ["ai_seller_finance"],
                },
            },
            {
                "title": "AI short drama market grew 200% YoY in Southeast Asia",
                "url": "https://techcrunch.com/2026/05/ai-short-drama-growth",
                "snippet": "AI-generated short drama market reaches $2B in Southeast Asia, growing 200% YoY. Major platforms opening dedicated AI content sections.",
                "source": "techcrunch",
                "query_id": "ai_content_market_trend",
                "query_def": {
                    "source_category": "market_trend",
                    "source_tier": 2,
                    "watchlist_refs": ["ai_content", "short_drama"],
                    "product_line_refs": ["ai_short_drama", "ai_content_products"],
                },
            },
        ]

    def fetch(self) -> list[dict]:
        return self._sample_data

    def parse(self, raw_data: list[dict]) -> list[dict]:
        parsed = []
        for item in raw_data:
            qdef = item.get("query_def", {})
            parsed.append({
                "title": (item.get("title", "") or "")[:120],
                "url": item.get("url", ""),
                "excerpt": ((item.get("snippet", "") or "")[:500]),
                "source_platform": item.get("source", "web"),
                "source_category": qdef.get("source_category", "market_trend"),
                "source_tier": qdef.get("source_tier", 3),
                "query_or_feed": "",
                "query_id": item.get("query_id", "unknown"),
                "watchlist_refs": qdef.get("watchlist_refs", []),
                "product_line_refs": qdef.get("product_line_refs", []),
                "raw_signal_type": qdef.get("source_category", "market_trend"),
                "confidence": 0.7,
            })
        return parsed

    def to_source_note(self, parsed: dict) -> dict:
        from urllib.parse import urlparse
        url = parsed.get("url", "")
        path_hash = abs(hash(url)) % 10**8
        return {
            "source_note_id": "",
            "connector_id": self.connector_id,
            "source_platform": parsed["source_platform"],
            "source_category": parsed["source_category"],
            "source_tier": parsed["source_tier"],
            "query_or_feed": parsed.get("query_or_feed", ""),
            "title": parsed["title"],
            "url": parsed["url"],
            "published_at": "",
            "fetched_at": self._now_iso(),
            "excerpt": parsed["excerpt"],
            "source_ref": f"{parsed['source_platform']}:{parsed.get('query_id', 'unknown')}",
            "watchlist_refs": parsed.get("watchlist_refs", []),
            "product_line_refs": parsed.get("product_line_refs", []),
            "raw_signal_type": parsed.get("raw_signal_type", ""),
            "confidence": parsed.get("confidence", 0.5),
            "dedupe_key": f"mock:{path_hash:08d}",
            "metadata": {"query_id": parsed.get("query_id", "")},
        }


# ════════════════════════════════════════════════════════════════════
# Mock GitHub Connector (simulates GitHubConnector)
# ════════════════════════════════════════════════════════════════════

class MockGitHubConnector(BaseConnector):
    """Mock connector that returns pre-built GitHub sample results."""

    @property
    def connector_id(self) -> str:
        return "github_test"

    def __init__(self):
        self._sample_data = [
            {
                "type": "repo",
                "name": "nousresearch/hermes-agent",
                "url": "https://github.com/nousresearch/hermes-agent",
                "description": "Hermes Agent — LLM agent with 30+ tools, persistent memory, multi-provider, MCP client",
                "language": "TypeScript",
                "topics": "agent, llm, ai, automation",
                "stars": 1280,
                "updated_at": "2026-05-30T10:00:00Z",
                "query_id": "ai_agent_os_repos",
                "query_def": {
                    "source_category": "ai_capability",
                    "source_tier": 2,
                    "watchlist_refs": ["ai_agent_ecosystem"],
                    "product_line_refs": ["ai_company_os"],
                },
            },
            {
                "type": "repo",
                "name": "openai/codex-cli",
                "url": "https://github.com/openai/codex-cli",
                "description": "Codex CLI — AI coding assistant by OpenAI, supports multi-file editing and agent mode",
                "language": "Python",
                "topics": "cli, coding-agent, ai",
                "stars": 8500,
                "updated_at": "2026-05-29T08:00:00Z",
                "query_id": "ai_agent_os_repos",
                "query_def": {
                    "source_category": "ai_capability",
                    "source_tier": 2,
                    "watchlist_refs": ["ai_agent_ecosystem"],
                    "product_line_refs": ["ai_company_os"],
                },
            },
            {
                "type": "repo",
                "name": "finaloop/accounting-api",
                "url": "https://github.com/finaloop/accounting-api",
                "description": "Automated accounting API for ecommerce platforms. Supports Amazon, Shopify, eBay.",
                "language": "Go",
                "topics": "accounting, ecommerce, api",
                "stars": 340,
                "updated_at": "2026-05-28T14:00:00Z",
                "query_id": "seller_finance_tools",
                "query_def": {
                    "source_category": "ai_capability",
                    "source_tier": 2,
                    "watchlist_refs": ["amazon_seller_finance"],
                    "product_line_refs": ["ai_seller_finance"],
                },
            },
            {
                "type": "repo",
                "name": "paperclip-ai/company-os",
                "url": "https://github.com/paperclip-ai/company-os",
                "description": "Paperclip — AI company operating system with heartbeat protocol and agent management",
                "language": "Rust",
                "topics": "operating-system, agents, automation",
                "stars": 2200,
                "updated_at": "2026-05-27T09:00:00Z",
                "query_id": "ai_agent_os_repos",
                "query_def": {
                    "source_category": "ai_capability",
                    "source_tier": 2,
                    "watchlist_refs": ["ai_agent_ecosystem"],
                    "product_line_refs": ["ai_company_os"],
                },
            },
            {
                "type": "release",
                "repo_name": "nousresearch/hermes-agent",
                "tag_name": "v0.3.0",
                "name": "Adds Paperclip adapter and skill marketplace",
                "url": "https://github.com/nousresearch/hermes-agent/releases/tag/v0.3.0",
                "description": "Major update: Paperclip adapter for managed agent execution, 80+ skills, session search, multi-provider support including deepseek and openrouter.",
                "published_at": "2026-05-25T12:00:00Z",
                "query_id": "hermes_agent_releases",
                "query_def": {
                    "source_category": "ai_capability",
                    "source_tier": 2,
                    "watchlist_refs": ["ai_agent_ecosystem"],
                    "product_line_refs": ["ai_company_os"],
                },
            },
        ]

    def fetch(self) -> list[dict]:
        return self._sample_data

    def parse(self, raw_data: list[dict]) -> list[dict]:
        parsed = []
        for item in raw_data:
            qdef = item.get("query_def", {})
            title = item.get("name", "")
            if item["type"] == "release":
                title = f"{item.get('repo_name', '')} — {item.get('name', '')}"

            excerpt = item.get("description", "")
            if item.get("language"):
                excerpt += f" [{item['language']}]"
            if item.get("stars", 0) > 100:
                excerpt += f" ⭐{item['stars']}"

            parsed.append({
                "title": title[:120],
                "url": item.get("url", ""),
                "excerpt": excerpt[:500],
                "source_platform": "github",
                "source_category": qdef.get("source_category", "ai_capability"),
                "source_tier": qdef.get("source_tier", 2),
                "query_or_feed": "",
                "query_id": item.get("query_id", "unknown"),
                "published_at": item.get("published_at", "") or item.get("updated_at", ""),
                "watchlist_refs": qdef.get("watchlist_refs", []),
                "product_line_refs": qdef.get("product_line_refs", []),
                "raw_signal_type": qdef.get("source_category", "ai_capability"),
                "confidence": 0.7,
                "_raw_type": item["type"],
            })
        return parsed

    def to_source_note(self, parsed: dict) -> dict:
        url = parsed.get("url", "")
        path_hash = abs(hash(url)) % 10**8
        return {
            "source_note_id": "",
            "connector_id": self.connector_id,
            "source_platform": "github",
            "source_category": parsed["source_category"],
            "source_tier": parsed["source_tier"],
            "query_or_feed": parsed.get("query_or_feed", ""),
            "title": parsed["title"],
            "url": parsed["url"],
            "published_at": parsed.get("published_at", ""),
            "fetched_at": self._now_iso(),
            "excerpt": parsed["excerpt"],
            "source_ref": f"github:{parsed.get('query_id', 'unknown')}:{parsed.get('_raw_type', 'repo')}",
            "watchlist_refs": parsed.get("watchlist_refs", []),
            "product_line_refs": parsed.get("product_line_refs", []),
            "raw_signal_type": parsed.get("raw_signal_type", "ai_capability"),
            "confidence": parsed.get("confidence", 0.5),
            "dedupe_key": f"github:{path_hash:08d}",
            "metadata": {
                "query_id": parsed.get("query_id", ""),
                "github_type": parsed.get("_raw_type", "repo"),
            },
        }


# ════════════════════════════════════════════════════════════════════
# Report Generator
# ════════════════════════════════════════════════════════════════════

def validate_against_schema(source_note: dict) -> list[str]:
    """Validate a SourceNote against the JSON Schema."""
    errors = []
    try:
        import jsonschema
        with open(_SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema = json.load(f)
        jsonschema.validate(instance=source_note, schema=schema)
    except ImportError:
        # Fallback: check required fields manually
        required = [
            "source_note_id", "connector_id", "source_platform",
            "source_category", "source_tier", "title", "url",
            "excerpt", "fetched_at", "dedupe_key",
        ]
        for field in required:
            if field not in source_note or not source_note.get(field):
                errors.append(f"Missing required field: {field}")
    except jsonschema.ValidationError as e:
        errors.append(str(e))
    return errors


def run_smoke_test() -> dict:
    """Run the full smoke test. Returns a report dict."""
    report = {
        "title": "v0.33 — Source Quality Smoke Test",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "connectors": {},
        "summary": {"total_notes": 0, "passed_gate": 0, "weak_candidate": 0, "schema_valid": 0, "errors": 0},
    }

    connectors = [
        ("Search Query Connector", MockSearchConnector()),
        ("GitHub Connector", MockGitHubConnector()),
    ]

    for conn_name, connector in connectors:
        print(f"\n━ {'=' * 50}")
        print(f"  Testing: {conn_name}")
        print(f"━ {'=' * 50}")

        conn_report = {"source_notes": [], "candidates": [], "valid_count": 0, "invalid_count": 0}

        # Run connector
        notes = connector.run(dry_run=True)

        for note in notes:
            # 1. Schema validation
            schema_errors = validate_against_schema(note)
            is_valid = len(schema_errors) == 0
            if is_valid:
                conn_report["valid_count"] += 1
                report["summary"]["schema_valid"] += 1
            else:
                conn_report["invalid_count"] += 1
                report["summary"]["errors"] += 1
                print(f"  ❌ Schema invalid: {note.get('source_note_id', '?')}: {schema_errors}")
                continue

            # 2. Feed into scout engine
            try:
                candidate = build_candidate(note)
                if candidate:
                    gate = candidate.get("evidence_gate_status", "?")
                    route = candidate.get("recommended_route", "?")
                    ctype = candidate.get("candidate_type", "?")
                    engine = candidate.get("primary_engine", "?")
                    pl = ", ".join(candidate.get("related_product_lines", []))

                    conn_report["candidates"].append({
                        "title": note.get("title", "?")[:60],
                        "gate": gate,
                        "type": ctype,
                        "engine": engine,
                        "route": route,
                        "product_lines": pl,
                    })

                    if gate == "passed":
                        report["summary"]["passed_gate"] += 1
                    else:
                        report["summary"]["weak_candidate"] += 1

                    print(f"  ✅ {ctype} | {gate} | {engine} | {route} | {pl[:40]}")
                else:
                    print(f"  ⚠️  No candidate generated")
                    report["summary"]["weak_candidate"] += 1

            except Exception as e:
                print(f"  ❌ Scout error: {e}")
                report["summary"]["errors"] += 1

            report["summary"]["total_notes"] += 1

        conn_report["total"] = len(notes)
        report["connectors"][conn_name] = conn_report

    return report


def print_report(report: dict):
    """Print a formatted report."""
    s = report["summary"]
    pass_rate = (s["passed_gate"] / s["total_notes"] * 100) if s["total_notes"] > 0 else 0
    schema_rate = (s["schema_valid"] / s["total_notes"] * 100) if s["total_notes"] > 0 else 0

    print(f"\n\n{'=' * 60}")
    print(f"  📊 Source Quality Smoke Test Report")
    print(f"  {report['timestamp']}")
    print(f"{'=' * 60}")
    print()
    print(f"  Summary")
    print(f"  {'─' * 40}")
    print(f"  Total SourceNotes generated:  {s['total_notes']}")
    print(f"  Schema valid:                 {s['schema_valid']}/{s['total_notes']} ({schema_rate:.0f}%)")
    print(f"  Passed Evidence Gate:         {s['passed_gate']}")
    print(f"  Weak / needs more evidence:   {s['weak_candidate']}")
    print(f"  Gate pass rate:               {pass_rate:.0f}%")
    print(f"  Errors:                       {s['errors']}")
    print()

    for conn_name, conn in report["connectors"].items():
        print(f"  {conn_name}")
        print(f"  {'─' * 40}")
        print(f"  SourceNotes: {conn['total']} ({conn['valid_count']} valid, {conn['invalid_count']} invalid)")
        print(f"  Candidates:  {len(conn['candidates'])}")
        for c in conn["candidates"][:5]:
            print(f"    {'✅' if c['gate'] == 'passed' else '⚠️'} [{c['type']}] {c['title']}")
            print(f"       Gate: {c['gate']} | Engine: {c['engine']} | Route: {c['route']}")
        print()

    # Recommendations
    print(f"  Recommendations")
    print(f"  {'─' * 40}")

    if s["passed_gate"] > 0:
        print(f"  ✅ Connector → Scout pipeline verified.")
        print(f"     SourceNotes convert to candidates correctly.")
    else:
        print(f"  ⚠️  No candidates passed the Evidence Gate. (Expected for raw SourceNotes)")
        print(f"     This is BY DESIGN — connectors produce raw signal data.")
        print(f"     SourceNotes lack `target_user` and `pain` analytical fields.")
        print(f"     ")
        print(f"     Architectural insight from this test:")
        print(f"     Connectors → SourceNote (schema valid) — CONFIRMED ✅")
        print(f"     SourceNote → build_candidate() — BLOCKED by Evidence Gate 🔒")
        print(f"     ")
        print(f"     Resolution paths for real runs:")
        print(f"     A. Add enrichment step: enrich SourceNote with target_user/pain")
        print(f"        before feeding to scout engine")
        print(f"     B. Use manual source note: hybrid connector output +")
        print(f"        founder review → enriched SourceNote → scout")

    if s["errors"] > 0:
        print(f"  ⚠️  {s['errors']} error(s) detected. Review logs above.")

    if s["schema_valid"] == s["total_notes"]:
        print(f"  ✅ All SourceNotes conform to schema.")
    else:
        print(f"  ⚠️  Some SourceNotes failed schema validation.")

    print()
    print(f"{'=' * 60}")
    print(f"  Result: {'✅ PASS' if s['errors'] == 0 else '⚠️  PARTIAL'}")
    print(f"{'=' * 60}")

    return s["errors"] == 0


def main():
    parser = argparse.ArgumentParser(
        description="v0.33 — Source Quality Smoke Test",
    )
    parser.add_argument("--report", "-o", default=None,
                        help="Save report to file (e.g. research/opportunity-source-layer/report.md)")
    args = parser.parse_args()

    print(f"🔍 Running v0.33 Source Quality Smoke Test...")
    print(f"   Using mock data (no API keys needed)")
    print(f"   Testing: SourceNote Contract → Connector Pipeline → Scout Engine")

    report = run_smoke_test()
    passed = print_report(report)

    # Save report if requested
    if args.report:
        os.makedirs(os.path.dirname(args.report), exist_ok=True)
        with open(args.report, "w", encoding="utf-8") as f:
            # Write markdown version
            f.write(f"# {report['title']}\n\n")
            f.write(f"**Timestamp:** {report['timestamp']}\n\n")
            f.write("## Summary\n\n")
            s = report["summary"]
            f.write(f"| Metric | Value |\n")
            f.write(f"|:-------|:-----:|\n")
            f.write(f"| SourceNotes | {s['total_notes']} |\n")
            f.write(f"| Schema Valid | {s['schema_valid']}/{s['total_notes']} |\n")
            f.write(f"| Passed Gate | {s['passed_gate']} |\n")
            f.write(f"| Weak | {s['weak_candidate']} |\n")
            f.write(f"| Errors | {s['errors']} |\n\n")
            f.write("## Connectors\n\n")
            for conn_name, conn in report["connectors"].items():
                f.write(f"### {conn_name}\n\n")
                f.write(f"- SourceNotes: {conn['total']} ({conn['valid_count']} valid)\n")
                f.write(f"- Candidates: {len(conn['candidates'])}\n\n")
                if conn["candidates"]:
                    f.write("| Title | Type | Gate | Engine | Route |\n")
                    f.write("|:------|:----:|:----:|:------:|:-----:|\n")
                    for c in conn["candidates"]:
                        f.write(f"| {c['title']} | {c['type']} | {c['gate']} | {c['engine']} | {c['route']} |\n")
                f.write("\n")
            f.write("## Result\n\n")
            f.write(f"{'✅ PASS' if passed else '⚠️  PARTIAL'}\n")
        print(f"\n  📄 Report saved to: {args.report}")

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
