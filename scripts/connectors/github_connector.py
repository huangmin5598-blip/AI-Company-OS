#!/usr/bin/env python3
"""
v0.33 — GitHub Connector

Searches GitHub for opportunity signals using the GitHub REST API.
Produces SourceNotes that feed into the v0.32 opportunity scout engine.

Supports 3 search modes:
  - repo_search: Search repos by keyword, sorted by stars/updated
  - topic_search: Search topics
  - release_search: Scan recent releases from tracked repos

API: api.github.com (works in China)
Auth: Optional token for higher rate limits. Set GITHUB_TOKEN env var.

Usage:
  python3 scripts/connectors/github_connector.py --dry-run
  python3 scripts/connectors/github_connector.py
  python3 scripts/connectors/github_connector.py --token ghp_xxx
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Optional

try:
    import yaml
except ImportError:
    print("❌ PyYAML required. Install: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

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

GITHUB_API = "https://api.github.com"


class GitHubConnector(BaseConnector):
    """Connector that searches GitHub for opportunity signals."""

    @property
    def connector_id(self) -> str:
        return "github"

    def __init__(self, config_path: str = None, token: str = None):
        """Initialize the GitHub connector.

        Args:
            config_path: Path to YAML query config.
            token: GitHub personal access token. Falls back to GITHUB_TOKEN env var.
        """
        self.config_path = config_path or self._find_config()
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self._queries = []
        self._load_queries()

    def _find_config(self) -> str:
        """Find the query config file."""
        if os.path.exists(_DEFAULT_CONFIG):
            return _DEFAULT_CONFIG
        if os.path.exists(_DEFAULT_EXAMPLE_CONFIG):
            return _DEFAULT_EXAMPLE_CONFIG
        return _DEFAULT_EXAMPLE_CONFIG

    def _load_queries(self):
        """Load GitHub queries from YAML config."""
        if not os.path.exists(self.config_path):
            print(f"  ⚠️  Query config not found: {self.config_path}")
            self._queries = []
            return
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            self._queries = data.get("github_queries", [])
            print(f"  📋 Loaded {len(self._queries)} GitHub queries from {self.config_path}")
        except Exception as e:
            print(f"  ❌ Error loading config: {e}")
            self._queries = []

    def _api_get(self, url: str) -> dict:
        """Make a GitHub API GET request."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Company-OS/1.0",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")[:200]
            if e.code == 403:
                print(f"      ❌ GitHub API rate limited. "
                      f"Set GITHUB_TOKEN for higher limits. ({body})")
            elif e.code == 422:
                print(f"      ❌ GitHub API validation error: {body}")
            else:
                print(f"      ❌ GitHub API error {e.code}: {body}")
            return {}
        except Exception as e:
            print(f"      ❌ GitHub request failed: {e}")
            return {}

    def fetch(self) -> list[dict]:
        """Execute all configured GitHub queries.

        Returns:
            list of raw result dicts from GitHub API.
        """
        all_results = []

        if not self._queries:
            print("  ⚠️  No GitHub queries configured.")
            return []

        for query_def in self._queries:
            query_id = query_def.get("id", "unknown")
            search_mode = query_def.get("search_mode", "repo_search")
            query_text = query_def.get("query", "")
            if not query_text:
                continue

            print(f"    Searching GitHub: [{query_id}] ({search_mode}: {query_text[:50]})...")

            if search_mode == "repo_search":
                results = self._search_repos(query_text, query_def)
            elif search_mode == "topic_search":
                results = self._search_topics(query_text, query_def)
            elif search_mode == "release_search":
                results = self._search_releases(query_text, query_def)
            else:
                print(f"      ⚠️  Unknown search_mode: {search_mode}")
                continue

            for r in results:
                r["_query_id"] = query_id
                r["_query_def"] = query_def
            all_results.extend(results)
            print(f"      → {len(results)} results")

        return all_results

    def _search_repos(self, query: str, query_def: dict) -> list[dict]:
        """Search GitHub repos by keyword."""
        import urllib.parse

        sort = query_def.get("sort", "stars")
        order = query_def.get("order", "desc")
        per_page = min(query_def.get("max_results", 10), 30)

        encoded = urllib.parse.quote(f"{query} in:name,description,topics")
        url = f"{GITHUB_API}/search/repositories?q={encoded}&sort={sort}&order={order}&per_page={per_page}"

        data = self._api_get(url)
        if not data:
            return []

        items = data.get("items", [])
        results = []
        for item in items[:per_page]:
            desc = (item.get("description") or "")[:300]
            lang = item.get("language") or ""
            topics = ", ".join(item.get("topics", [])[:5])
            results.append({
                "type": "repo",
                "name": item.get("full_name", ""),
                "url": item.get("html_url", ""),
                "description": desc,
                "language": lang,
                "topics": topics,
                "stars": item.get("stargazers_count", 0),
                "updated_at": item.get("updated_at", ""),
                "created_at": item.get("created_at", ""),
            })
        return results

    def _search_topics(self, query: str, query_def: dict) -> list[dict]:
        """Search GitHub topics."""
        import urllib.parse

        per_page = min(query_def.get("max_results", 10), 30)
        encoded = urllib.parse.quote(query)
        url = f"{GITHUB_API}/search/topics?q={encoded}&per_page={per_page}"
        headers = {
            "Accept": "application/vnd.github.mercy-preview+json",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"      ❌ Topic search failed: {e}")
            return []

        items = data.get("items", [])
        results = []
        for item in items[:per_page]:
            results.append({
                "type": "topic",
                "name": item.get("name", ""),
                "url": f"https://github.com/topics/{item.get('name', '')}",
                "description": (item.get("description") or "")[:300],
                "created_at": item.get("created_at", ""),
                "updated_at": item.get("updated_at", ""),
                "score": item.get("score", 0),
            })
        return results

    def _search_releases(self, query: str, query_def: dict) -> list[dict]:
        """Scan recent releases from repos matching a query.

        First finds repos matching the query, then scans their latest releases.
        """
        import urllib.parse
        per_page = min(query_def.get("max_results", 5), 10)
        releases_per_repo = min(query_def.get("releases_per_repo", 3), 5)

        # Find repos
        encoded = urllib.parse.quote(f"{query} in:name,description")
        repo_url = f"{GITHUB_API}/search/repositories?q={encoded}&sort=updated&order=desc&per_page={per_page}"
        repo_data = self._api_get(repo_url)
        if not repo_data:
            return []

        repos = repo_data.get("items", [])[:per_page]
        results = []

        for repo in repos:
            repo_full = repo.get("full_name", "")
            release_url = f"{GITHUB_API}/repos/{repo_full}/releases?per_page={releases_per_repo}"

            release_data = self._api_get(release_url)
            if not release_data:
                continue

            for release in (release_data if isinstance(release_data, list) else [])[:releases_per_repo]:
                body = (release.get("body") or "")[:300]
                results.append({
                    "type": "release",
                    "repo_name": repo_full,
                    "repo_url": repo.get("html_url", ""),
                    "tag_name": release.get("tag_name", ""),
                    "name": release.get("name", "") or release.get("tag_name", ""),
                    "url": release.get("html_url", ""),
                    "description": body,
                    "published_at": release.get("published_at", ""),
                })

        return results

    def parse(self, raw_data: list[dict]) -> list[dict]:
        """Parse raw GitHub results into structured dicts."""
        parsed_items = []

        for item in raw_data:
            query_def = item.get("_query_def", {})

            # Determine title and excerpt based on result type
            if item["type"] == "repo":
                title = item.get("name", "")
                excerpt = item.get("description", "")
                extra = ""
                if item.get("language"):
                    extra += f" [{item['language']}]"
                if item.get("stars", 0) > 100:
                    extra += f" ⭐{item['stars']}"
                if item.get("topics"):
                    extra += f" topics: {item['topics']}"
                excerpt = f"{excerpt}{extra}"[:300]

            elif item["type"] == "topic":
                title = f"Topic: {item.get('name', '')}"
                excerpt = item.get("description", "")

            elif item["type"] == "release":
                title = f"{item.get('repo_name', '')} — {item.get('name', '')}"
                excerpt = item.get("description", "")[:300]

            else:
                continue

            if not excerpt:
                continue

            parsed = {
                "title": title[:120],
                "url": item.get("url", ""),
                "excerpt": excerpt[:500],
                "source_platform": "github",
                "source_category": query_def.get("source_category", "ai_capability"),
                "source_tier": query_def.get("source_tier", 2),
                "query_or_feed": query_def.get("query", ""),
                "query_id": item.get("_query_id", "unknown"),
                "published_at": item.get("published_at", "") or item.get("updated_at", "") or item.get("created_at", ""),
                "watchlist_refs": query_def.get("watchlist_refs", []),
                "product_line_refs": query_def.get("product_line_refs", []),
                "raw_signal_type": query_def.get("source_category", "ai_capability"),
                "confidence": self._calculate_confidence(item, query_def),
                "_raw_type": item["type"],
            }
            parsed_items.append(parsed)

        return parsed_items

    def _calculate_confidence(self, item: dict, query_def: dict) -> float:
        """Calculate confidence for a GitHub result."""
        confidence = 0.5  # Base

        # Repos with high stars are more credible
        if item.get("type") == "repo":
            stars = item.get("stars", 0)
            if stars > 1000:
                confidence += 0.3
            elif stars > 100:
                confidence += 0.2
            elif stars > 10:
                confidence += 0.1

        # Repos with description are more useful
        if item.get("description"):
            confidence += 0.1

        # Topics found
        if item.get("topics"):
            confidence += 0.1

        # Release notes with substantial content
        if item.get("type") == "release":
            body_len = len(item.get("description", ""))
            if body_len > 200:
                confidence += 0.1
            if body_len > 500:
                confidence += 0.1

        return min(confidence, 1.0)

    def to_source_note(self, parsed: dict) -> dict:
        """Convert parsed GitHub item into a valid SourceNote."""
        url = parsed.get("url", "")
        path_hash = abs(hash(url)) % 10**8
        dedupe = f"github:{path_hash:08d}"

        note = {
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
            "dedupe_key": dedupe,
            "metadata": {
                "query_id": parsed.get("query_id", ""),
                "github_type": parsed.get("_raw_type", "repo"),
            },
        }
        return note


# ════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="v0.33 — GitHub Connector",
    )
    parser.add_argument("--config", "-c", default=None,
                        help="Path to query config YAML")
    parser.add_argument("--token", default=None,
                        help="GitHub personal access token (or set GITHUB_TOKEN env var)")
    parser.add_argument("--output-dir", "-o", default=None,
                        help="Override output directory")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Preview SourceNotes without writing")
    args = parser.parse_args()

    connector = GitHubConnector(
        config_path=args.config,
        token=args.token,
    )
    connector.run(output_dir=args.output_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
