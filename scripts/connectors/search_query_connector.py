#!/usr/bin/env python3
"""
v0.33 — Search Query Connector

Searches the web for opportunity signals using configurable queries.
Produces SourceNotes that feed into the v0.32 opportunity scout engine.

Reads query profiles from a YAML config file.
Supports multiple search backends: tavily (default), duckduckgo (fallback).

Usage:
  python3 scripts/connectors/search_query_connector.py --dry-run
  python3 scripts/connectors/search_query_connector.py
  python3 scripts/connectors/search_query_connector.py --config config/opportunity-source-queries.yaml
"""

import argparse
import json
import os
import re
import sys
import urllib.parse
from datetime import datetime, timezone
from typing import Optional

# ── Dependencies ──
try:
    import yaml
except ImportError:
    print("❌ PyYAML required. Install: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# ── Parent import ──
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)
try:
    from base_connector import BaseConnector
except ImportError:
    sys.path.insert(0, os.path.join(_SCRIPT_DIR, ".."))
    from scripts.connectors.base_connector import BaseConnector


_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))
_DEFAULT_CONFIG = os.path.join(_PROJECT_ROOT, "config", "opportunity-source-queries.yaml")
_DEFAULT_EXAMPLE_CONFIG = os.path.join(_PROJECT_ROOT, "config", "opportunity-source-queries.example.yaml")


class SearchQueryConnector(BaseConnector):
    """Connector that runs web searches for opportunity signals."""

    @property
    def connector_id(self) -> str:
        return "search_query"

    def __init__(self, config_path: str = None, api_key: str = None, backend: str = "tavily"):
        """Initialize the search query connector.

        Args:
            config_path: Path to YAML query config. Falls back to real config,
                         then example config.
            api_key: Search API key. If None, checks TAVILY_API_KEY env var.
            backend: Search backend. 'tavily' (default) or 'duckduckgo'.
        """
        self.config_path = config_path or self._find_config()
        self.api_key = api_key or os.environ.get("TAVILY_API_KEY", "")
        self.backend = backend
        self._queries = []
        self._load_queries()

    def _find_config(self) -> str:
        """Find the query config file, preferring real config over example."""
        if os.path.exists(_DEFAULT_CONFIG):
            return _DEFAULT_CONFIG
        if os.path.exists(_DEFAULT_EXAMPLE_CONFIG):
            return _DEFAULT_EXAMPLE_CONFIG
        return _DEFAULT_EXAMPLE_CONFIG  # Will show a helpful error

    def _load_queries(self):
        """Load search queries from YAML config."""
        if not os.path.exists(self.config_path):
            print(f"  ⚠️  Query config not found: {self.config_path}", file=sys.stderr)
            print(f"     Create {_DEFAULT_CONFIG} or use the example at {_DEFAULT_EXAMPLE_CONFIG}",
                  file=sys.stderr)
            self._queries = []
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            self._queries = data.get("search_queries", [])
            print(f"  📋 Loaded {len(self._queries)} queries from {self.config_path}")
        except Exception as e:
            print(f"  ❌ Error loading config: {e}", file=sys.stderr)
            self._queries = []

    def fetch(self) -> list[dict]:
        """Fetch search results for all configured queries.

        Returns:
            list of raw search result dicts, each with:
                query_id, query, title, url, snippet/description, source
        """
        all_results = []

        if not self._queries:
            print("  ⚠️  No queries configured. Nothing to fetch.")
            return []

        for query_def in self._queries:
            query_id = query_def.get("id", "unknown")
            query_text = query_def.get("query", "")
            if not query_text:
                continue

            print(f"    Searching: [{query_id}] {query_text[:60]}...")
            try:
                results = self._search(query_text, query_def)
                for r in results:
                    r["_query_id"] = query_id
                    r["_query_def"] = query_def
                all_results.extend(results)
                print(f"      → {len(results)} results")
            except Exception as e:
                print(f"      ❌ Search failed: {e}")

        return all_results

    def _search(self, query: str, query_def: dict) -> list[dict]:
        """Execute a single search query.

        Supports: tavily (default), duckduckgo (fallback).
        """
        if self.backend == "tavily" and self.api_key:
            return self._search_tavily(query, query_def)
        elif self.backend == "duckduckgo":
            return self._search_duckduckgo(query, query_def)
        else:
            print(f"      ⚠️  No search backend available. "
                  f"Set TAVILY_API_KEY env var or use --backend duckduckgo")
            return []

    def _search_tavily(self, query: str, query_def: dict) -> list[dict]:
        """Search via Tavily API."""
        import urllib.request

        url = "https://api.tavily.com/search"
        payload = json.dumps({
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": 5,
            "include_answer": False,
            "include_raw_content": False,
        }).encode("utf-8")

        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            results = []
            for item in data.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", ""),
                    "source": self._classify_platform(item.get("url", "")),
                    "published_date": item.get("published_date", ""),
                })
            return results

        except urllib.error.HTTPError as e:
            print(f"      ❌ Tavily API error: {e.code} {e.read().decode()[:200]}")
            return []
        except Exception as e:
            print(f"      ❌ Tavily request failed: {e}")
            return []

    def _search_duckduckgo(self, query: str, query_def: dict) -> list[dict]:
        """Search via DuckDuckGo HTML (no API key needed, less reliable)."""
        import urllib.request
        from html.parser import HTMLParser

        encoded = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                html = resp.read().decode("utf-8")

            # Simple extraction of result links (not full HTML parsing)
            results = []
            # Find result blocks by looking for <a class="result__a"
            pattern = r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>'
            hrefs = re.findall(pattern, html, re.DOTALL)

            snippets = re.findall(
                r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
                html, re.DOTALL,
            )

            for i, (href, title_html) in enumerate(hrefs[:5]):
                # Clean title from HTML tags
                title = re.sub(r'<[^>]+>', '', title_html).strip()
                snippet = ""
                if i < len(snippets):
                    snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip()

                results.append({
                    "title": title,
                    "url": href,
                    "snippet": snippet,
                    "source": self._classify_platform(href),
                    "published_date": "",
                })

            return results

        except Exception as e:
            print(f"      ❌ DuckDuckGo search failed: {e}")
            return []

    def _classify_platform(self, url: str) -> str:
        """Determine the source platform from a URL."""
        url_lower = url.lower()
        if "reddit.com" in url_lower:
            return "reddit"
        elif "github.com" in url_lower:
            return "github"
        elif "producthunt.com" in url_lower:
            return "product_hunt"
        elif "g2.com" in url_lower:
            return "g2"
        elif "techcrunch.com" in url_lower:
            return "techcrunch"
        elif "hackernews" in url_lower or "news.ycombinator.com" in url_lower:
            return "hacker_news"
        elif "zhihu.com" in url_lower:
            return "zhihu"
        elif "shopify.com" in url_lower or "shopify.dev" in url_lower:
            return "shopify"
        elif "roblox.com" in url_lower:
            return "roblox"
        elif "twitter.com" in url_lower or "x.com" in url_lower:
            return "twitter"
        elif "youtube.com" in url_lower:
            return "youtube"
        elif "medium.com" in url_lower or "substack.com" in url_lower:
            return "blog"
        else:
            return "web"

    def parse(self, raw_data: list[dict]) -> list[dict]:
        """Parse raw search results into structured dicts.

        Each parsed dict has fields ready for to_source_note().
        """
        parsed_items = []

        for item in raw_data:
            query_def = item.get("_query_def", {})
            query_id = item.get("_query_id", "unknown")

            excerpt = item.get("snippet", "") or item.get("description", "") or ""
            excerpt = excerpt.strip()
            if not excerpt:
                continue

            parsed = {
                "title": (item.get("title", "") or "")[:120],
                "url": item.get("url", ""),
                "excerpt": excerpt[:500],
                "source_platform": item.get("source", "web"),
                "source_category": query_def.get("source_category", "market_trend"),
                "source_tier": query_def.get("source_tier", 3),
                "query_or_feed": query_def.get("query", ""),
                "query_id": query_id,
                "published_at": item.get("published_date", ""),
                "watchlist_refs": query_def.get("watchlist_refs", []),
                "product_line_refs": query_def.get("product_line_refs", []),
                "raw_signal_type": query_def.get("source_category", "market_trend"),
                "confidence": self._calculate_confidence(item, query_def),
            }
            parsed_items.append(parsed)

        return parsed_items

    def _calculate_confidence(self, item: dict, query_def: dict) -> float:
        """Calculate confidence score for a search result (0.0–1.0)."""
        confidence = 0.5  # Base

        # Source platform boosts
        platform = item.get("source", "")
        if platform in ("reddit", "github", "g2"):
            confidence += 0.2
        elif platform in ("product_hunt", "techcrunch"):
            confidence += 0.1

        # Has a substantial excerpt
        excerpt = item.get("snippet", "") or item.get("description", "") or ""
        if len(excerpt) > 100:
            confidence += 0.1
        if len(excerpt) > 200:
            confidence += 0.1

        # Exact title match suggests relevance
        title = item.get("title", "")
        query = query_def.get("query", "").lower()
        query_words = set(query.split())
        title_words = set(title.lower().split())
        overlap = len(query_words & title_words)
        if overlap >= 3:
            confidence += 0.1

        return min(confidence, 1.0)

    def to_source_note(self, parsed: dict) -> dict:
        """Convert parsed search result into a valid SourceNote."""
        from urllib.parse import urlparse

        # Generate dedupe key
        url = parsed.get("url", "")
        parsed_url = urlparse(url)
        path_hash = abs(hash(url)) % 10**8
        dedupe = f"{parsed['source_platform']}:{path_hash:08d}"

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
            "source_ref": f"{parsed['source_platform']}:{parsed.get('query_id', 'unknown')}",
            "watchlist_refs": parsed.get("watchlist_refs", []),
            "product_line_refs": parsed.get("product_line_refs", []),
            "raw_signal_type": parsed.get("raw_signal_type", parsed["source_category"]),
            "confidence": parsed.get("confidence", 0.5),
            "dedupe_key": dedupe,
            "metadata": {
                "query_id": parsed.get("query_id", ""),
            },
        }
        return note


# ════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="v0.33 — Search Query Connector",
    )
    parser.add_argument("--config", "-c", default=None,
                        help="Path to query config YAML")
    parser.add_argument("--backend", default="tavily",
                        choices=["tavily", "duckduckgo"],
                        help="Search backend (default: tavily)")
    parser.add_argument("--output-dir", "-o", default=None,
                        help="Override output directory")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Preview SourceNotes without writing")
    parser.add_argument("--api-key", default=None,
                        help="Tavily API key (or set TAVILY_API_KEY env var)")
    args = parser.parse_args()

    connector = SearchQueryConnector(
        config_path=args.config,
        api_key=args.api_key,
        backend=args.backend,
    )

    connector.run(output_dir=args.output_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
