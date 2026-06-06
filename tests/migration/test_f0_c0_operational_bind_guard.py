from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

from conftest import OPERATIONAL_DB, REPO_ROOT, load_f0_env


class OperationalBindGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.harness = load_f0_env()

    def _url(self, path: Path) -> str:
        return f"sqlite:///{path}"

    def test_refuses_operational_path_before_engine_creation(self) -> None:
        configuration = {"sqlalchemy.url": self._url(OPERATIONAL_DB)}
        with mock.patch.object(self.harness, "engine_from_config") as engine_factory:
            with self.assertRaises(self.harness.OperationalDatabaseBindRefused):
                self.harness.create_guarded_connectable(
                    configuration,
                    environ={},
                )
            engine_factory.assert_not_called()

    def test_refuses_relative_operational_alias(self) -> None:
        relative = OPERATIONAL_DB.relative_to(REPO_ROOT)
        with self.assertRaises(self.harness.OperationalDatabaseBindRefused):
            self.harness.assert_operational_db_bind_allowed(
                f"sqlite:///{relative}",
                environ={},
                working_directory=REPO_ROOT,
            )

    def test_refuses_symlink_alias(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            alias = Path(temporary_directory) / "operational-alias.db"
            alias.symlink_to(OPERATIONAL_DB)
            with self.assertRaises(self.harness.OperationalDatabaseBindRefused):
                self.harness.assert_operational_db_bind_allowed(
                    self._url(alias),
                    environ={},
                )

    def test_allows_temporary_database(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database = Path(temporary_directory) / "temporary.db"
            resolved = self.harness.assert_operational_db_bind_allowed(
                self._url(database),
                environ={},
            )
            self.assertEqual(database.resolve(), resolved)

    def test_explicit_flag_allows_bind_but_does_not_write(self) -> None:
        before = self.harness.build_source_manifest(OPERATIONAL_DB)
        configuration = {"sqlalchemy.url": self._url(OPERATIONAL_DB)}
        sentinel = object()
        with mock.patch.object(
            self.harness,
            "engine_from_config",
            return_value=sentinel,
        ) as engine_factory:
            result = self.harness.create_guarded_connectable(
                configuration,
                environ={self.harness.OPERATIONAL_BIND_FLAG: "1"},
            )
        after = self.harness.build_source_manifest(OPERATIONAL_DB)

        self.assertIs(sentinel, result)
        engine_factory.assert_called_once()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
