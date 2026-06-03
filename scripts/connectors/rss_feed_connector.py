#!/usr/bin/env python3
"""
v0.36 — RSS/Atom Feed Connector

Fetches signal source entries from configured RSS/Atom feeds.
Produces SourceNotes that feed into the v0.35 opportunity evaluation engine.

Two buckets:
  Bucket A: AI Seller Finance 产品线 feeds（主线）
  Bucket B: AI Company OS 自身进化 feeds（副线）

Usage:
  python3 scripts/connectors/rss_feed_connector.py --dry-run
  python3 scripts/connectors/rss_feed_connector.py
  python3 scripts/connectors/rss_feed_connector.py --config config/opportunity-source-feeds.yaml
  python3 scripts/connectors/rss_feed_connector.py --bucket A
  python3 scripts/connectors/rss_feed_connector.py --bucket B
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from typing import Optional

# ── Dependencies ──
try:
    import yaml
except ImportError:
    print("❌ PyYAML required. Install: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

try:
    import feedparser
except ImportError:
    print("❌ feedparser required. Install: pip install feedparser", file=sys.stderr)
    sys.exit(1)

# ── Parent import ──
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))

sys.path.insert(0, os.path.join(_SCRIPT_DIR, ".."))
try:
    from scripts.connectors.base_connector import BaseConnector  # noqa: E402
except ImportError:
    from connectors.base_connector import BaseConnector  # noqa: E402

_DEFAULT_CONFIG = os.path.join(_PROJECT_ROOT, "config", "opportunity-source-feeds.yaml")
_DEFAULT_OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "research", "opportunity-source-notes")


def classify_platform(url: str, feed_title: str = "") -> str:
    """Determine the source platform from a URL or feed title."""
    url_lower = url.lower()
    if "openai.com" in url_lower: return "openai"
    elif "github.blog" in url_lower or "github.com" in url_lower: return "github"
    elif "microsoft.com" in url_lower or "blogs.microsoft" in url_lower: return "microsoft"
    elif "google.com" in url_lower or "googleblog" in url_lower or "blog.research.google" in url_lower or "developers.googleblog" in url_lower: return "google"
    elif "aboutamazon.com" in url_lower or "amazon.com" in url_lower or "amazon." in url_lower: return "amazon"
    elif "junglescout.com" in url_lower: return "jungle_scout"
    elif "sellerapp.com" in url_lower: return "sellerapp"
    elif "sellerboard.com" in url_lower: return "sellerboard"
    elif "getida.com" in url_lower: return "getida"
    elif "salesforce.com" in url_lower: return "salesforce"
    elif "anthropic.com" in url_lower: return "anthropic"
    elif "medium.com" in url_lower: return "medium"
    elif "reddit.com" in url_lower: return "reddit"
    return "web"


class RSSFeedConnector(BaseConnector):
    """Connector that fetches opportunity signals from RSS/Atom feeds."""

    def __init__(self, config_path: str = None, bucket: str = None):
        self.config_path = config_path or _DEFAULT_CONFIG
        self.bucket_filter = bucket  # 'A', 'B', or None (all)
        self._feeds = []
        self._load_feeds()

    @property
    def connector_id(self) -> str:
        return "rss_feed"

    def _load_feeds(self):
        """Load feed configurations from YAML."""
        if not os.path.exists(self.config_path):
            print(f"  ⚠️  Feed config not found: {self.config_path}", file=sys.stderr)
            print(f"     Create {_DEFAULT_CONFIG} with your feed URLs", file=sys.stderr)
            self._feeds = []
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            all_feeds = data.get("rss_feeds", [])

            if self.bucket_filter:
                self._feeds = [f for f in all_feeds if f.get("bucket") == self.bucket_filter]
                bucket_label = f"Bucket {self.bucket_filter}"
            else:
                self._feeds = all_feeds
                bucket_label = "all buckets"

            print(f"  📋 Loaded {len(self._feeds)} feeds ({bucket_label}) from {self.config_path}")
        except Exception as e:
            print(f"  ❌ Error loading feed config: {e}", file=sys.stderr)
            self._feeds = []

    def fetch(self) -> list[dict]:
        """Fetch entries from all configured RSS feeds."""
        all_entries = []

        if not self._feeds:
            print("  ⚠️  No feeds configured. Nothing to fetch.")
            return []

        for feed_def in self._feeds:
            feed_id = feed_def.get("id", "unknown")
            feed_url = feed_def.get("feed_url", "")
            max_entries = min(feed_def.get("max_entries", 10), 20)

            if not feed_url:
                continue

            print(f"    Fetching: [{feed_id}] {feed_url[:80]}...")
            try:
                parsed = feedparser.parse(feed_url)

                if parsed.bozo and not parsed.entries:
                    print(f"      ⚠️  Feed parse error (bozo): {parsed.bozo_exception}")
                    continue

                entries = parsed.entries[:max_entries]
                for entry in entries:
                    all_entries.append({
                        "_feed_id": feed_id,
                        "_feed_def": feed_def,
                        "_feed_title": parsed.feed.get("title", ""),
                        "title": entry.get("title", ""),
                        "url": entry.get("link", ""),
                        "snippet": (entry.get("summary", "") or entry.get("description", "") or entry.get("content", [{}])[0].get("value", "") if entry.get("content") else "")[:500],
                        "published_date": entry.get("published", "") or entry.get("updated", "") or "",
                        "authors": entry.get("authors", [{"name": ""}])[0].get("name", "") if entry.get("authors") else "",
                    })

                print(f"      → {len(entries)} entries ({len(parsed.entries)} total in feed)")
            except Exception as e:
                print(f"      ❌ Feed fetch failed: {e}")

        return all_entries

    def parse(self, raw_data: list[dict]) -> list[dict]:
        """Parse raw feed entries into structured dicts ready for SourceNotes."""
        parsed_items = []

        for item in raw_data:
            feed_def = item.get("_feed_def", {})
            feed_id = item.get("_feed_id", "unknown")

            excerpt = item.get("snippet", "").strip()
            # Clean HTML from excerpt
            excerpt = re.sub(r'<[^>]+>', '', excerpt)
            excerpt = re.sub(r'\s+', ' ', excerpt).strip()[:500]

            if not excerpt:
                # Fall back to title-only signal
                excerpt = f"[Feed entry] {item.get('title', '')}"

            parsed = {
                "title": (item.get("title", "") or "")[:120],
                "url": item.get("url", ""),
                "excerpt": excerpt[:500],
                "source_platform": classify_platform(item.get("url", ""), feed_def.get("name", "")),
                "source_category": feed_def.get("source_category", "market_trend"),
                "source_tier": feed_def.get("source_tier", 3),
                "query_or_feed": feed_def.get("name", ""),
                "feed_id": feed_id,
                "published_at": item.get("published_date", ""),
                "authors": item.get("authors", ""),
                "watchlist_refs": feed_def.get("watchlist_refs", []),
                "product_line_refs": feed_def.get("product_line_refs", []),
                "bucket": feed_def.get("bucket", "?"),
                "raw_signal_type": feed_def.get("source_category", "market_trend"),
                "confidence": self._calculate_confidence(item, feed_def),
            }
            parsed_items.append(parsed)

        return parsed_items

    def _calculate_confidence(self, item: dict, feed_def: dict) -> float:
        """Calculate confidence score for a feed entry (0.0–1.0)."""
        confidence = 0.6  # RSS feeds are generally more reliable than search

        # Tier-based boost
        tier = feed_def.get("source_tier", 3)
        if tier == 1:
            confidence += 0.2
        elif tier == 2:
            confidence += 0.1

        # Excerpt quality
        excerpt = item.get("snippet", "") or ""
        if len(excerpt) > 200:
            confidence += 0.1
        elif len(excerpt) < 50:
            confidence -= 0.1  # Minimal content

        # Has both title and URL
        if item.get("title") and item.get("url"):
            confidence += 0.05

        return min(confidence, 1.0)

    def to_source_note(self, parsed: dict) -> dict:
        """Convert parsed feed entry into a valid SourceNote."""
        from urllib.parse import urlparse

        url = parsed.get("url", "")
        parsed_url = urlparse(url)
        path_hash = abs(hash(url)) % 10**8
        dedupe = f"rss:{parsed['source_platform']}:{path_hash:08d}"

        note = {
            "source_note_id": "",  # Will be set by run()
            "connector_id": self.connector_id,
            "source_platform": parsed["source_platform"],
            "source_category": parsed["source_category"],
            "source_tier": parsed["source_tier"],
            "query_or_feed": parsed.get("query_or_feed", ""),
            "title": parsed["title"],
            "url": parsed["url"],
            "published_at": parsed.get("published_at", ""),
            "fetched_at": self._now_iso(),
            "excerpt": parsed["excerpt"],
            "source_ref": f"rss:{parsed.get('feed_id', 'unknown')}",
            "watchlist_refs": parsed.get("watchlist_refs", []),
            "product_line_refs": parsed.get("product_line_refs", []),
            "raw_signal_type": parsed.get("raw_signal_type", parsed["source_category"]),
            "confidence": parsed.get("confidence", 0.6),
            "dedupe_key": dedupe,
            "metadata": {
                "feed_id": parsed.get("feed_id", ""),
                "bucket": parsed.get("bucket", "?"),
                "authors": parsed.get("authors", ""),
            },
        }
        return note


# ════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="v0.36 — RSS/Atom Feed Connector",
    )
    parser.add_argument("--config", "-c", default=None,
                        help="Path to feed config YAML")
    parser.add_argument("--bucket", "-b", default=None,
                        choices=["A", "B"],
                        help="Filter to specific bucket (A or B)")
    parser.add_argument("--output-dir", "-o", default=None,
                        help="Override output directory")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Preview SourceNotes without writing")
    args = parser.parse_args()

    connector = RSSFeedConnector(
        config_path=args.config,
        bucket=args.bucket,
    )

    connector.run(output_dir=args.output_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
