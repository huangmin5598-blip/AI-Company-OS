from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
import tempfile
import unittest

from path_bootstrap import ensure_backend_path


ensure_backend_path()

from app.pilot.bootstrap import bootstrap_pilot_database  # noqa: E402
from app.pilot.database import PilotDatabase  # noqa: E402
from app.pilot.real_workbench import RealWorkbenchStore  # noqa: E402


FORBIDDEN_KEYS = {
    "storage_ref",
    "scratch_root",
    "scratch_path",
    "result_ref",
    "database_path",
    "operational_db_path",
}
FORBIDDEN_VALUE_FRAGMENTS = (
    "/Users/",
    "backend/data",
    "private/",
    ".ai-company-os/pilot/vs001-pilot.db",
)


def _walk(value):
    if isinstance(value, Mapping):
        for key, nested in value.items():
            yield ("key", str(key))
            yield from _walk(nested)
    elif isinstance(value, str):
        yield ("value", value)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            yield from _walk(item)


class RealWorkbenchPublicBoundaryTests(unittest.TestCase):
    def test_envelope_exposes_no_private_paths_or_storage_refs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = PilotDatabase.for_disposable_test(
                Path(temporary) / "vs001-pilot.db"
            )
            try:
                bootstrap_pilot_database(database)
                with database.command_session() as session:
                    envelope = RealWorkbenchStore(session).create_run(
                        "clip_matrix_agent",
                        "Plan a private-safe clip matrix pilot.",
                    )
            finally:
                database.dispose()

        for kind, item in _walk(envelope):
            if kind == "key":
                self.assertNotIn(item, FORBIDDEN_KEYS)
            if kind == "value":
                for fragment in FORBIDDEN_VALUE_FRAGMENTS:
                    self.assertNotIn(fragment, item)

    def test_governance_remains_pilot_only_and_non_public_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = PilotDatabase.for_disposable_test(
                Path(temporary) / "vs001-pilot.db"
            )
            try:
                bootstrap_pilot_database(database)
                with database.command_session() as session:
                    run = RealWorkbenchStore(session).create_run(
                        "spoken_agent_offer",
                        "Create a persistent spoken agent workbench plan.",
                    )
            finally:
                database.dispose()

        self.assertEqual("pilot_non_authoritative", run["authority"])
        self.assertTrue(run["governance"]["pilot_only"])
        self.assertFalse(run["governance"]["operational_authority"])
        self.assertFalse(run["governance"]["public_safe"])
        self.assertFalse(run["governance"]["real_runtime_invoked"])
        self.assertFalse(run["governance"]["scheduler_invoked"])
        self.assertFalse(run["governance"]["worker_pool_invoked"])


if __name__ == "__main__":
    unittest.main()
