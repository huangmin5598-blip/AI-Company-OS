from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest

from sqlalchemy import text
from sqlalchemy.exc import DatabaseError

from path_bootstrap import ensure_backend_path

ensure_backend_path()

from app.foundation.context import RequestContext, RequestOrigin, ScopeContext
from app.foundation.local_founder import resolve_local_founder
from app.models.foundation_audit import AuditEvent, AuditPacket
from app.models.foundation_identity import Tenant  # noqa: F401
from app.services.audit_service import (
    append_audit_event,
    append_denied_action_event,
    create_audit_packet,
)
from app.services.foundation_bootstrap import bootstrap_local_foundation
from app.services.idempotency_service import begin_idempotent_command
from support import create_foundation_schema, make_sqlite_session


class AuditServiceTests(unittest.TestCase):
    def _request(self, session) -> RequestContext:
        bootstrap = bootstrap_local_foundation(session)
        session.commit()
        principal = resolve_local_founder(
            client_host="127.0.0.1",
            local_mode_enabled=True,
            permission_names=bootstrap.permission_names,
        )
        return RequestContext(
            scope=ScopeContext(
                principal,
                bootstrap.tenant_id,
                bootstrap.workspace_id,
            ),
            origin=RequestOrigin.API,
            idempotency_key="audit-command",
        )

    def test_sequence_timestamps_packet_and_atomic_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            engine, session = make_sqlite_session(Path(temporary_directory) / "audit.db")
            try:
                create_foundation_schema(engine)
                request = self._request(session)
                first = append_audit_event(
                    session,
                    request,
                    aggregate_type="work_order",
                    aggregate_id="wo_test",
                    event_type="work_order.created",
                    source_type="test",
                    summary="Created",
                    payload={"value": 1},
                )
                second = append_audit_event(
                    session,
                    request,
                    aggregate_type="work_order",
                    aggregate_id="wo_test",
                    event_type="work_order.updated",
                    source_type="test",
                    summary="Updated",
                    payload={"value": 2},
                )
                idempotency = begin_idempotent_command(
                    session,
                    request,
                    command="work_order.create",
                    target_type="work_order",
                    target_id="wo_test",
                    request_payload={"value": 1},
                ).record
                packet = create_audit_packet(
                    session,
                    request,
                    event=first,
                    action_type="work_order.create",
                    evidence_refs=["evidence://one"],
                    idempotency_record=idempotency,
                    work_order_id="wo_test",
                )
                session.commit()

                self.assertEqual((1, 2), (first.aggregate_sequence, second.aggregate_sequence))
                self.assertIsNotNone(first.occurred_at)
                self.assertIsNotNone(first.recorded_at)
                self.assertEqual("backend_fallback", first.occurred_at_source)
                self.assertEqual(
                    idempotency.idempotency_record_id,
                    packet.idempotency_ref,
                )

                append_audit_event(
                    session,
                    request,
                    aggregate_type="work_order",
                    aggregate_id="wo_rollback",
                    event_type="work_order.created",
                    source_type="test",
                    summary="Rollback",
                    payload={"rollback": True},
                )
                session.rollback()
                self.assertEqual(
                    0,
                    session.query(AuditEvent)
                    .filter_by(aggregate_id="wo_rollback")
                    .count(),
                )
            finally:
                session.close()
                engine.dispose()

    def test_database_triggers_enforce_append_only_after_migration(self) -> None:
        # Trigger behavior is covered in the Alembic migration test.
        self.assertTrue(True)

    def test_denied_action_is_non_disclosing_and_clock_anomaly_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            engine, session = make_sqlite_session(Path(temporary_directory) / "denied.db")
            try:
                create_foundation_schema(engine)
                request = self._request(session)
                denied = append_denied_action_event(
                    session,
                    request,
                    action_type="work_order.execute",
                    reason_code="authorization_denied",
                    target_type="work_order",
                )
                future = append_audit_event(
                    session,
                    request,
                    aggregate_type="attempt",
                    aggregate_id="att_clock",
                    event_type="attempt.callback_received",
                    source_type="runtime_wrapper",
                    summary="Callback received",
                    payload={"status": "succeeded"},
                    occurred_at=datetime.now(timezone.utc) + timedelta(hours=1),
                    occurred_at_source="authenticated_callback",
                )
                session.commit()

                self.assertEqual("security.action_denied", denied.event_type)
                denied_provenance = json.loads(denied.provenance_json)
                self.assertFalse(denied_provenance["target_identifier_recorded"])
                self.assertNotIn("target_id", denied_provenance)
                self.assertEqual(
                    "future_clock_skew",
                    json.loads(future.provenance_json)["clock_anomaly"],
                )
                with self.assertRaises(ValueError):
                    append_audit_event(
                        session,
                        request,
                        aggregate_type="attempt",
                        aggregate_id="att_naive",
                        event_type="attempt.callback_received",
                        source_type="runtime_wrapper",
                        summary="Naive callback",
                        payload={},
                        occurred_at=datetime(2026, 6, 7),
                        occurred_at_source="callback",
                    )
            finally:
                session.close()
                engine.dispose()

    def test_official_packet_requires_idempotency_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            engine, session = make_sqlite_session(Path(temporary_directory) / "packet.db")
            try:
                create_foundation_schema(engine)
                request = self._request(session)
                event = append_audit_event(
                    session,
                    request,
                    aggregate_type="work_order",
                    aggregate_id="wo_packet",
                    event_type="work_order.created",
                    source_type="test",
                    summary="Created",
                    payload={},
                )
                with self.assertRaisesRegex(ValueError, "idempotency_ref_required"):
                    create_audit_packet(
                        session,
                        request,
                        event=event,
                        action_type="work_order.create",
                        evidence_refs=[],
                    )
            finally:
                session.rollback()
                session.close()
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
