from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from conftest import load_f0_env


class SourceManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.harness = load_f0_env()

    def _create_database(self, root: Path) -> Path:
        path = root / "source.db"
        with sqlite3.connect(path) as connection:
            connection.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY)")
            connection.execute("INSERT INTO sample DEFAULT VALUES")
        return path

    def test_records_present_and_absent_components(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database = self._create_database(Path(temporary_directory))
            manifest = self.harness.build_source_manifest(database)
            components = manifest["source_database"]["components"]

            self.assertEqual(["db", "wal", "shm"], [item["role"] for item in components])
            self.assertTrue(components[0]["present"])
            self.assertIsInstance(components[0]["size_bytes"], int)
            self.assertIsInstance(components[0]["mtime_ns"], int)
            self.assertEqual(64, len(components[0]["sha256"]))
            for absent in components[1:]:
                self.assertFalse(absent["present"])
                self.assertIsNone(absent["size_bytes"])
                self.assertIsNone(absent["mtime_ns"])
                self.assertIsNone(absent["sha256"])

    def test_records_wal_and_shm_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database = self._create_database(Path(temporary_directory))
            Path(f"{database}-wal").write_bytes(b"wal-test")
            Path(f"{database}-shm").write_bytes(b"shm-test")
            manifest = self.harness.build_source_manifest(database)
            components = manifest["source_database"]["components"]

            self.assertTrue(components[1]["present"])
            self.assertTrue(components[2]["present"])
            self.assertEqual(hashlib.sha256(b"wal-test").hexdigest(), components[1]["sha256"])
            self.assertEqual(hashlib.sha256(b"shm-test").hexdigest(), components[2]["sha256"])

    def test_composite_hash_is_canonical_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database = self._create_database(Path(temporary_directory))
            first = self.harness.build_source_manifest(database)
            second = self.harness.build_source_manifest(database)

            self.assertEqual(first, second)
            expected_payload = dict(first)
            actual_hash = expected_payload.pop("composite_manifest_hash")
            canonical = self.harness.canonical_json_bytes(expected_payload)
            self.assertFalse(canonical.endswith(b"\n"))
            self.assertEqual(
                actual_hash,
                "sha256:" + hashlib.sha256(canonical).hexdigest(),
            )
            parsed = json.loads(canonical.decode("utf-8"))
            self.assertEqual(expected_payload, parsed)

    def test_fails_closed_when_source_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database = self._create_database(Path(temporary_directory))

            def mutate_between_snapshots() -> None:
                with database.open("ab") as target:
                    target.write(b"unstable")

            with self.assertRaises(self.harness.SourceManifestUnstable):
                self.harness.build_source_manifest(
                    database,
                    stability_probe=mutate_between_snapshots,
                )


if __name__ == "__main__":
    unittest.main()
