from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest

from alembic import command
from alembic.config import Config

from conftest import OPERATIONAL_DB, REPO_ROOT, load_f0_env


class InertBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.harness = load_f0_env()

    def _config(self, database: Path) -> Config:
        configuration = Config(str(REPO_ROOT / "alembic.ini"))
        configuration.set_main_option("sqlalchemy.url", f"sqlite:///{database}")
        return configuration

    def test_baseline_upgrades_only_disposable_database_and_is_inert(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database = Path(temporary_directory) / "baseline.db"
            command.upgrade(self._config(database), "0001_baseline")

            with sqlite3.connect(database) as connection:
                tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master "
                        "WHERE type='table' ORDER BY name"
                    )
                }
                revision = connection.execute(
                    "SELECT version_num FROM alembic_version"
                ).fetchone()[0]

            self.assertEqual({"alembic_version"}, tables)
            self.assertEqual("0001_baseline", revision)

    def test_operational_database_is_never_stamped_or_migrated(self) -> None:
        before = self.harness.build_source_manifest(OPERATIONAL_DB)
        with self.assertRaisesRegex(Exception, "operational_db_bind_refused"):
            command.upgrade(self._config(OPERATIONAL_DB), "head")
        after = self.harness.build_source_manifest(OPERATIONAL_DB)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
