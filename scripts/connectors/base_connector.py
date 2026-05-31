#!/usr/bin/env python3
"""
v0.33 — Base Connector Interface

Abstract base class for all signal source connectors.

Every connector must implement:
  - fetch()        → Fetch raw data from the source
  - parse()        → Parse raw data into structured dicts
  - to_source_note() → Convert a parsed dict into a valid SourceNote
  - dedupe_key()   → Return a unique deduplication key

Connectors NEVER generate candidates. They produce SourceNotes.
The scout engine (v0.32 opportunity_scout.py) handles all judging and scoring.
"""

import json
import os
import sys
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional


_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))
_DEFAULT_OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "research", "opportunity-source-notes")


class BaseConnector(ABC):
    """Abstract base class for all signal source connectors."""

    @property
    @abstractmethod
    def connector_id(self) -> str:
        """Unique identifier for this connector. e.g. 'search_query', 'github'."""
        pass

    @abstractmethod
    def fetch(self) -> list[dict]:
        """Fetch raw data from the source.

        Returns:
            list of raw data dicts. Each dict's structure depends on the connector.
        """
        pass

    @abstractmethod
    def parse(self, raw_data: list[dict]) -> list[dict]:
        """Parse raw data into structured dicts ready for to_source_note().

        Args:
            raw_data: Output from fetch()

        Returns:
            list of parsed dicts with fields ready for SourceNote conversion.
        """
        pass

    @abstractmethod
    def to_source_note(self, parsed: dict) -> dict:
        """Convert a single parsed item into a valid SourceNote dict.

        The returned dict must conform to config/schemas/source_note.schema.json.

        Args:
            parsed: A single item from parse()

        Returns:
            A valid SourceNote dict.
        """
        pass

    def dedupe_key(self, source_note: dict) -> str:
        """Return a unique deduplication key for this source note.

        Default: use the source_note's own dedupe_key field.
        Override if the connector needs custom dedup logic.

        Args:
            source_note: A complete SourceNote dict

        Returns:
            A string key unique to this source.
        """
        return source_note.get("dedupe_key", source_note.get("source_note_id", ""))

    def validate(self, source_note: dict) -> list[str]:
        """Validate a SourceNote against basic contract rules.

        Returns:
            List of validation error messages. Empty list = valid.
        """
        errors = []
        required = [
            "source_note_id", "connector_id", "source_platform",
            "source_category", "source_tier", "title", "url",
            "excerpt", "fetched_at", "dedupe_key",
        ]
        for field in required:
            if field not in source_note or not source_note.get(field):
                errors.append(f"Missing required field: {field}")

        # Category check
        valid_categories = [
            "user_complaint", "ai_capability", "market_trend",
            "platform_shift", "asset_scan", "os_feedback",
        ]
        cat = source_note.get("source_category", "")
        if cat and cat not in valid_categories:
            errors.append(f"Invalid source_category: {cat}")

        # Tier check
        tier = source_note.get("source_tier", 0)
        if tier not in (1, 2, 3):
            errors.append(f"source_tier must be 1, 2, or 3, got: {tier}")

        # Excerpt length
        excerpt = source_note.get("excerpt", "")
        if len(excerpt) > 500:
            errors.append(f"excerpt too long: {len(excerpt)} chars (max 500)")

        return errors

    def _now_iso(self) -> str:
        """Return current UTC time in ISO 8601."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _generate_id(self, seq: int = 1) -> str:
        """Generate a source_note_id in format SN-{connector_id}-{YYYYMMDD}-{NNN}."""
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        return f"SN-{self.connector_id}-{today}-{seq:03d}"

    def run(self, output_dir: str = None, dry_run: bool = False) -> list[dict]:
        """Full pipeline: fetch → parse → to_source_note for all items.

        Args:
            output_dir: Override output directory (default: research/opportunity-source-notes/)
            dry_run: If True, print summary without writing files

        Returns:
            List of valid SourceNote dicts that were generated.
        """
        output_dir = output_dir or _DEFAULT_OUTPUT_DIR

        print(f"  🔌 [{self.connector_id}] Fetching...")
        raw_data = self.fetch()

        if not raw_data:
            print(f"  ⚠️  [{self.connector_id}] No raw data returned")
            return []

        print(f"  🔌 [{self.connector_id}] Parsing {len(raw_data)} items...")
        parsed_items = self.parse(raw_data)

        if not parsed_items:
            print(f"  ⚠️  [{self.connector_id}] No items parsed")
            return []

        source_notes = []
        seq = 1
        for item in parsed_items:
            try:
                note = self.to_source_note(item)
                # Override auto-generated ID if not set
                if "source_note_id" not in note or not note.get("source_note_id"):
                    note["source_note_id"] = self._generate_id(seq)

                # Validate
                errors = self.validate(note)
                if errors:
                    print(f"  ⚠️  [{self.connector_id}] Validation failed for item {seq}:")
                    for e in errors:
                        print(f"       - {e}")
                    seq += 1
                    continue

                source_notes.append(note)
                seq += 1

            except Exception as e:
                print(f"  ⚠️  [{self.connector_id}] Error processing item {seq}: {e}")
                seq += 1
                continue

        # Deduplicate within this batch
        seen_keys = set()
        unique_notes = []
        for note in source_notes:
            key = self.dedupe_key(note)
            if key in seen_keys:
                print(f"  ⚠️  [{self.connector_id}] Duplicate skipped: {key}")
                continue
            seen_keys.add(key)
            unique_notes.append(note)

        print(f"  🔌 [{self.connector_id}] Generated {len(unique_notes)} unique SourceNotes "
              f"({len(source_notes) - len(unique_notes)} duplicates skipped)")

        # Write output
        if not dry_run:
            connector_dir = os.path.join(output_dir, self.connector_id)
            os.makedirs(connector_dir, exist_ok=True)

            written = 0
            for note in unique_notes:
                filepath = os.path.join(connector_dir, f"{note['source_note_id']}.json")
                try:
                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(note, f, ensure_ascii=False, indent=2)
                    written += 1
                except Exception as e:
                    print(f"  ❌ [{self.connector_id}] Write error for {note['source_note_id']}: {e}")

            print(f"  ✅ [{self.connector_id}] Written {written}/{len(unique_notes)} SourceNotes "
                  f"to {connector_dir}")
        else:
            print(f"  📋 DRY RUN — would write {len(unique_notes)} SourceNotes to "
                  f"{output_dir}/{self.connector_id}/")
            for note in unique_notes[:3]:
                print(f"     {note['source_note_id']}: {note.get('title', '?')[:60]}...")
            if len(unique_notes) > 3:
                print(f"     ... and {len(unique_notes) - 3} more")

        return unique_notes
