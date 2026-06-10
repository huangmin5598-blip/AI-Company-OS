"""Physical database boundary for the non-authoritative VS-001 pilot."""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import sqlite3
import tempfile
from typing import Iterator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


REPO_ROOT = Path(__file__).resolve().parents[3]
PILOT_DB_PATH = (
    REPO_ROOT / ".ai-company-os/pilot/vs001-pilot.db"
).resolve(strict=False)
OPERATIONAL_DB_PATH = (
    REPO_ROOT / "backend/data/ai_company_os.db"
).resolve(strict=False)
PILOT_AUTHORITY = "pilot_non_authoritative"
PILOT_MARKER_ID = "vs001"
EXPECTED_OPERATIONAL_SHA256 = (
    "d1dd452f8bd64bac859e48ff7721b8e5131bc9193cd2e9f34a63b30fb43bc4df"
)


class PilotBoundaryViolation(RuntimeError):
    pass


def _same_inode(left: Path, right: Path) -> bool:
    if not left.exists() or not right.exists():
        return False
    left_stat = left.stat()
    right_stat = right.stat()
    return (
        left_stat.st_dev == right_stat.st_dev
        and left_stat.st_ino == right_stat.st_ino
    )


def assert_fixed_pilot_path(path: Path) -> Path:
    candidate = path.expanduser()
    if candidate.is_symlink():
        raise PilotBoundaryViolation("pilot_database_symlink_forbidden")
    resolved = candidate.resolve(strict=False)
    if resolved != PILOT_DB_PATH:
        raise PilotBoundaryViolation("pilot_database_path_not_authorized")
    current = resolved.parent
    while current != REPO_ROOT:
        if current.is_symlink():
            raise PilotBoundaryViolation("pilot_database_parent_symlink_forbidden")
        if current.parent == current:
            raise PilotBoundaryViolation("pilot_database_outside_repository")
        current = current.parent
    if resolved == OPERATIONAL_DB_PATH or _same_inode(resolved, OPERATIONAL_DB_PATH):
        raise PilotBoundaryViolation("operational_database_binding_refused")
    return resolved


def _sqlite_authorizer(
    action: int,
    _arg1: str | None,
    _arg2: str | None,
    _database: str | None,
    _trigger: str | None,
) -> int:
    if action in {sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH}:
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


def _configure_connection(dbapi_connection, _connection_record) -> None:
    dbapi_connection.execute("PRAGMA foreign_keys=ON")
    dbapi_connection.set_authorizer(_sqlite_authorizer)


class PilotDatabase:
    def __init__(self, path: Path | None = None, *, test_only: bool = False):
        if test_only:
            if path is None:
                raise ValueError("test_pilot_path_required")
            if path.is_symlink():
                raise PilotBoundaryViolation("test_pilot_symlink_forbidden")
            resolved = path.resolve(strict=False)
            temp_root = Path(tempfile.gettempdir()).resolve()
            if os.path.commonpath((str(resolved), str(temp_root))) != str(
                temp_root
            ):
                raise PilotBoundaryViolation("test_pilot_path_outside_temp")
            if resolved.name != "vs001-pilot.db":
                raise PilotBoundaryViolation("test_pilot_filename_mismatch")
            if _same_inode(resolved, OPERATIONAL_DB_PATH):
                raise PilotBoundaryViolation("operational_database_binding_refused")
            self.path = resolved
        else:
            self.path = assert_fixed_pilot_path(path or PILOT_DB_PATH)
        self.engine: Engine = create_engine(f"sqlite:///{self.path}")
        event.listen(self.engine, "connect", _configure_connection)
        self.session_factory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
        )

    @classmethod
    def for_disposable_test(cls, path: Path) -> "PilotDatabase":
        return cls(path, test_only=True)

    def assert_single_database(self, session: Session) -> None:
        rows = session.execute(text("PRAGMA database_list")).all()
        attached = [(row[1], row[2]) for row in rows if row[1] != "temp"]
        if len(attached) != 1 or attached[0][0] != "main":
            raise PilotBoundaryViolation("pilot_cross_database_binding_refused")
        actual = Path(attached[0][1]).resolve(strict=False)
        if actual != self.path:
            raise PilotBoundaryViolation("pilot_database_binding_mismatch")
        if _same_inode(actual, OPERATIONAL_DB_PATH):
            raise PilotBoundaryViolation("operational_database_binding_refused")

    def require_authority(self, session: Session) -> None:
        self.assert_single_database(session)
        rows = session.execute(
            text(
                "SELECT authority FROM pilot_marker"
                " WHERE marker_id=:marker_id"
            ),
            {"marker_id": PILOT_MARKER_ID},
        ).scalars().all()
        total = session.execute(
            text("SELECT COUNT(*) FROM pilot_marker")
        ).scalar_one()
        if total != 1 or rows != [PILOT_AUTHORITY]:
            raise PilotBoundaryViolation("pilot_marker_authority_invalid")
        asset_component = session.execute(
            text(
                "SELECT version, authority FROM pilot_schema_components"
                " WHERE component='assets'"
            )
        ).all()
        if asset_component != [("vs002-1", PILOT_AUTHORITY)]:
            raise PilotBoundaryViolation("pilot_asset_schema_version_invalid")

    @contextmanager
    def command_session(self) -> Iterator[Session]:
        session = self.session_factory()
        try:
            self.require_authority(session)
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def dispose(self) -> None:
        self.engine.dispose()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def operational_hash_status() -> dict[str, object]:
    actual = sha256_file(OPERATIONAL_DB_PATH)
    return {
        "expected_sha256": EXPECTED_OPERATIONAL_SHA256,
        "actual_sha256": actual,
        "matches": actual == EXPECTED_OPERATIONAL_SHA256,
    }


__all__ = [
    "EXPECTED_OPERATIONAL_SHA256",
    "OPERATIONAL_DB_PATH",
    "PILOT_AUTHORITY",
    "PILOT_DB_PATH",
    "PILOT_MARKER_ID",
    "PilotBoundaryViolation",
    "PilotDatabase",
    "assert_fixed_pilot_path",
    "operational_hash_status",
]
