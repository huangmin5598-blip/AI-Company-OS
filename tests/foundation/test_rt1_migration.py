from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.models.foundation_audit import (
    AuditAggregateSequence,
    AuditEvent,
    AuditPacket,
    IdempotencyRecord,
)
from app.models.foundation_identity import (
    FoundationUser,
    Membership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
    Tenant,
    Workspace,
)

from support import OPERATIONAL_DB, REPO_ROOT, load_f0_env


EXPECTED_TABLES = {
    "alembic_version",
    "audit_aggregate_sequences",
    "audit_events",
    "audit_packets",
    "idempotency_records",
    "membership_roles",
    "memberships",
    "permissions",
    "role_permissions",
    "roles",
    "tenants",
    "users",
    "workspaces",
}

FOUNDATION_MODELS = (
    Tenant,
    Workspace,
    FoundationUser,
    Membership,
    Role,
    Permission,
    RolePermission,
    MembershipRole,
    IdempotencyRecord,
    AuditAggregateSequence,
    AuditEvent,
    AuditPacket,
)


class RT1MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.harness = load_f0_env()

    def _config(self, database: Path) -> Config:
        configuration = Config(str(REPO_ROOT / "alembic.ini"))
        configuration.set_main_option("sqlalchemy.url", f"sqlite:///{database}")
        return configuration

    def test_upgrade_and_downgrade_disposable_database(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database = Path(temporary_directory) / "rt1.db"
            config = self._config(database)
            command.upgrade(config, "head")
            with sqlite3.connect(database) as connection:
                tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                }
                revision = connection.execute(
                    "SELECT version_num FROM alembic_version"
                ).fetchone()[0]
                triggers = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='trigger'"
                    )
                }
            self.assertEqual(EXPECTED_TABLES, tables)
            self.assertEqual("0002_identity_scope_audit", revision)
            self.assertEqual(
                {
                    "audit_events_no_update",
                    "audit_events_no_delete",
                    "audit_packets_no_update",
                    "audit_packets_no_delete",
                },
                triggers,
            )

            command.downgrade(config, "0001_baseline")
            with sqlite3.connect(database) as connection:
                remaining = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                }
            self.assertEqual({"alembic_version"}, remaining)

    def test_migration_columns_match_foundation_models(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database = Path(temporary_directory) / "model-contract.db"
            command.upgrade(self._config(database), "head")
            engine = create_engine(f"sqlite:///{database}")
            try:
                database_inspector = inspect(engine)
                for model in FOUNDATION_MODELS:
                    migrated_columns = {
                        column["name"]
                        for column in database_inspector.get_columns(
                            model.__tablename__
                        )
                    }
                    model_columns = {
                        column.name
                        for column in model.__table__.columns
                    }
                    self.assertEqual(
                        model_columns,
                        migrated_columns,
                        model.__tablename__,
                    )
            finally:
                engine.dispose()

    def test_operational_database_remains_refused(self) -> None:
        before = self.harness.build_source_manifest(OPERATIONAL_DB)
        with self.assertRaisesRegex(Exception, "operational_db_bind_refused"):
            command.upgrade(self._config(OPERATIONAL_DB), "head")
        self.assertEqual(before, self.harness.build_source_manifest(OPERATIONAL_DB))

    def test_append_only_triggers_reject_update_and_delete(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database = Path(temporary_directory) / "append-only.db"
            command.upgrade(self._config(database), "head")
            with sqlite3.connect(database) as connection:
                connection.execute(
                    "INSERT INTO tenants "
                    "(tenant_id,name,slug,status,created_by,updated_by) "
                    "VALUES ('ten_test','Test','test','active','test','test')"
                )
                connection.execute(
                    "INSERT INTO workspaces "
                    "(workspace_id,tenant_id,name,slug,status,created_by,updated_by) "
                    "VALUES ('wsp_test','ten_test','Test','test','active','test','test')"
                )
                connection.execute(
                    "INSERT INTO audit_events "
                    "(audit_event_id,tenant_id,workspace_id,scope_key,"
                    "aggregate_type,aggregate_id,aggregate_sequence,event_type,"
                    "occurred_at,recorded_at,occurred_at_source,actor_type,"
                    "actor_id,mode,source_type,correlation_id,summary,payload_hash,"
                    "provenance_json) "
                    "VALUES ('aud_test','ten_test','wsp_test','ten_test:wsp_test',"
                    "'test','one',1,'test.created',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,"
                    "'backend_fallback','human','test','os_governed','test','cor_test',"
                    "'created','sha256:test','{}')"
                )
                connection.commit()
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(
                        "UPDATE audit_events SET summary='changed' "
                        "WHERE audit_event_id='aud_test'"
                    )
                connection.rollback()
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(
                        "DELETE FROM audit_events WHERE audit_event_id='aud_test'"
                    )


if __name__ == "__main__":
    unittest.main()
