"""F0-C0 inert Alembic environment and read-only source guards."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Callable, Mapping

from alembic import context
from sqlalchemy import MetaData, engine_from_config, pool
from sqlalchemy.engine import make_url


REPO_ROOT = Path(__file__).resolve().parents[1]
OPERATIONAL_DB_PATH = (REPO_ROOT / "backend/data/ai_company_os.db").resolve()
OPERATIONAL_BIND_FLAG = "AI_COMPANY_OS_ALLOW_OPERATIONAL_DB_BIND"
IMPORT_ONLY_FLAG = "F0_C0_IMPORT_ONLY"
COMPONENT_ORDER = ("db", "wal", "shm")

# FC-1: do not import backend models or Base in F0-C0.
target_metadata = MetaData()


class SourceManifestUnstable(RuntimeError):
    """Raised when source components change during one manifest capture."""


class OperationalDatabaseBindRefused(RuntimeError):
    """Raised before engine creation when the operational DB is not allowed."""


def canonical_json_bytes(payload: Mapping[str, object]) -> bytes:
    """Serialize canonical JSON as UTF-8 with no trailing newline."""
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _component_path(db_path: Path, role: str) -> Path:
    if role == "db":
        return db_path
    return Path(f"{db_path}-{role}")


def _component_record(db_path: Path, role: str) -> dict[str, object]:
    path = _component_path(db_path, role)
    if not path.exists():
        return {
            "role": role,
            "path": str(path),
            "present": False,
            "size_bytes": None,
            "mtime_ns": None,
            "sha256": None,
        }
    if not path.is_file():
        raise SourceManifestUnstable(f"SQLite component is not a file: {path}")

    before = path.stat()
    sha256 = _hash_file(path)
    after = path.stat()
    before_signature = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    )
    after_signature = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    )
    if before_signature != after_signature:
        raise SourceManifestUnstable(f"SQLite component changed while hashing: {path}")

    return {
        "role": role,
        "path": str(path),
        "present": True,
        "size_bytes": int(after.st_size),
        "mtime_ns": int(after.st_mtime_ns),
        "sha256": sha256,
    }


def _capture_components_once(db_path: Path) -> list[dict[str, object]]:
    return [_component_record(db_path, role) for role in COMPONENT_ORDER]


def _detect_journal_mode(db_path: Path) -> str:
    if not db_path.is_file():
        return "unknown"
    before = db_path.stat()
    with db_path.open("rb") as source:
        header = source.read(20)
    after = db_path.stat()
    if (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    ) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        raise SourceManifestUnstable(
            f"SQLite database changed while reading header: {db_path}"
        )
    if len(header) < 20 or header[:16] != b"SQLite format 3\x00":
        return "unknown"
    if header[18] == 2 or header[19] == 2:
        return "wal"
    if header[18] == 1 and header[19] == 1:
        return "delete"
    return "other"


def build_source_manifest(
    database_path: str | os.PathLike[str],
    *,
    quiesced: bool = False,
    stability_probe: Callable[[], None] | None = None,
) -> dict[str, object]:
    """Build a deterministic WAL/SHM-aware manifest without SQLite writes."""
    db_path = Path(database_path).expanduser().resolve()
    first_components = _capture_components_once(db_path)
    first_journal_mode = _detect_journal_mode(db_path)
    if stability_probe is not None:
        stability_probe()
    second_components = _capture_components_once(db_path)
    second_journal_mode = _detect_journal_mode(db_path)

    if (
        first_components != second_components
        or first_journal_mode != second_journal_mode
    ):
        raise SourceManifestUnstable(
            "SQLite source changed between stability snapshots"
        )

    payload: dict[str, object] = {
        "schema_version": "f0-c0-source-manifest-v1",
        "canonicalization": {
            "encoding": "UTF-8",
            "sorted_keys": True,
            "separators": [",", ":"],
            "trailing_newline": False,
            "component_order": list(COMPONENT_ORDER),
            "absent_component_fields": "explicit_null",
        },
        "source_database": {
            "canonical_path": str(db_path),
            "journal_mode": first_journal_mode,
            "quiesced": bool(quiesced),
            "components": first_components,
        },
    }
    payload["composite_manifest_hash"] = (
        "sha256:" + hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    )
    return payload


def sqlite_database_path(
    database_url: str,
    *,
    working_directory: str | os.PathLike[str] | None = None,
) -> Path | None:
    """Resolve a SQLite URL to its canonical file path."""
    url = make_url(database_url)
    if not url.drivername.startswith("sqlite"):
        raise ValueError("F0-C0 supports SQLite URLs only")
    if not url.database or url.database == ":memory:":
        return None
    path = Path(url.database).expanduser()
    if not path.is_absolute():
        path = Path(working_directory or Path.cwd()) / path
    return path.resolve()


def assert_operational_db_bind_allowed(
    database_url: str,
    *,
    environ: Mapping[str, str] | None = None,
    operational_db_path: str | os.PathLike[str] = OPERATIONAL_DB_PATH,
    working_directory: str | os.PathLike[str] | None = None,
) -> Path | None:
    """Fail before engine creation for an unapproved operational DB bind."""
    requested_path = sqlite_database_path(
        database_url,
        working_directory=working_directory,
    )
    if requested_path is None:
        return None

    operational_path = Path(operational_db_path).expanduser().resolve()
    effective_environ = os.environ if environ is None else environ
    if (
        requested_path == operational_path
        and effective_environ.get(OPERATIONAL_BIND_FLAG) != "1"
    ):
        raise OperationalDatabaseBindRefused(
            "operational_db_bind_refused: set "
            f"{OPERATIONAL_BIND_FLAG}=1 only under separate authorization"
        )
    return requested_path


def create_guarded_connectable(
    configuration: Mapping[str, str],
    *,
    prefix: str = "sqlalchemy.",
    environ: Mapping[str, str] | None = None,
):
    """Run the bind guard before SQLAlchemy creates an engine."""
    database_url = configuration.get(f"{prefix}url", "")
    assert_operational_db_bind_allowed(database_url, environ=environ)
    return engine_from_config(
        configuration,
        prefix=prefix,
        poolclass=pool.NullPool,
    )


def run_migrations_offline() -> None:
    url = context.config.get_main_option("sqlalchemy.url")
    assert_operational_db_bind_allowed(url)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = context.config.get_section(
        context.config.config_ini_section,
    ) or {}
    connectable = create_guarded_connectable(configuration)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if os.environ.get(IMPORT_ONLY_FLAG) != "1":
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
