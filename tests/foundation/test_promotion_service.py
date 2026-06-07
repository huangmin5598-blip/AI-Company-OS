from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from path_bootstrap import ensure_backend_path

ensure_backend_path()

from app.foundation.authorization import AuthorizationDenied
from app.foundation.context import (
    AuthenticationMethod,
    PrincipalContext,
    PrincipalType,
    RequestContext,
    RequestOrigin,
    ScopeContext,
)
from app.foundation.local_founder import resolve_local_founder
from app.models.foundation_audit import AuditEvent
from app.models.foundation_execution import PromotionRecord
from app.services.foundation_bootstrap import bootstrap_local_foundation
from app.services.promotion_service import promote_native_output
from support import create_foundation_schema, make_sqlite_session


class PromotionServiceTests(unittest.TestCase):
    def _request(self, session, *, key: str = "promote-1") -> RequestContext:
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
            idempotency_key=key,
            mode="promotion",
        )

    def test_promotion_is_idempotent_audited_and_candidate_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            engine, session = make_sqlite_session(
                Path(temporary_directory) / "promotion.db"
            )
            try:
                create_foundation_schema(engine)
                request = self._request(session)
                arguments = {
                    "intake_id": "intake_native_1",
                    "source_conversation_ref": "conversation://native/1",
                    "source_provider": "codex",
                    "source_domain": "general",
                    "promotion_rationale": "Founder selected the proposal",
                    "target_object_type": "work_order",
                    "accepted_context_refs": ["context://accepted"],
                    "rejected_context_refs": ["context://rejected"],
                    "review_required": True,
                }
                first = promote_native_output(session, request, **arguments)
                session.commit()
                replay = promote_native_output(session, request, **arguments)

                self.assertFalse(first.replay)
                self.assertTrue(replay.replay)
                self.assertEqual(first.record.promotion_id, replay.record.promotion_id)
                self.assertEqual("native", first.record.original_mode)
                self.assertEqual("promotion", first.record.promoted_mode)
                self.assertTrue(first.record.review_required)
                self.assertEqual(1, session.query(PromotionRecord).count())
                event = session.get(AuditEvent, first.record.audit_event_ref)
                self.assertEqual("native_output.promoted", event.event_type)
                self.assertIsNone(first.record.target_work_order_id)
            finally:
                session.close()
                engine.dispose()

    def test_native_mode_and_sensitive_source_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            engine, session = make_sqlite_session(
                Path(temporary_directory) / "promotion-deny.db"
            )
            try:
                create_foundation_schema(engine)
                request = self._request(session, key="promote-deny")
                with self.assertRaisesRegex(ValueError, "promotion_mode_required"):
                    promote_native_output(
                        session,
                        RequestContext(
                            scope=request.scope,
                            origin=RequestOrigin.API,
                            idempotency_key="native-mode",
                            mode="native",
                        ),
                        intake_id="intake_native_2",
                        source_conversation_ref="conversation://native/2",
                        source_provider="hermes",
                        source_domain="general",
                        promotion_rationale="Candidate only",
                        target_object_type="intake",
                        accepted_context_refs=[],
                        rejected_context_refs=[],
                        review_required=True,
                    )

                restricted_principal = PrincipalContext(
                    principal_id="operator",
                    principal_type=PrincipalType.HUMAN,
                    authentication_method=AuthenticationMethod.SESSION,
                    tenant_id=request.scope.tenant_id,
                    workspace_id=request.scope.workspace_id,
                    permission_names=frozenset({"promotion.create"}),
                )
                restricted = RequestContext(
                    scope=ScopeContext(
                        restricted_principal,
                        request.scope.tenant_id,
                        request.scope.workspace_id,
                    ),
                    origin=RequestOrigin.API,
                    idempotency_key="sensitive",
                    mode="promotion",
                )
                with self.assertRaises(AuthorizationDenied):
                    promote_native_output(
                        session,
                        restricted,
                        intake_id="intake_support",
                        source_conversation_ref="support://conversation/1",
                        source_provider="gpt",
                        source_domain="support",
                        promotion_rationale="Support insight",
                        target_object_type="opportunity",
                        accepted_context_refs=[],
                        rejected_context_refs=[],
                        review_required=True,
                    )
                self.assertEqual(0, session.query(PromotionRecord).count())
            finally:
                session.rollback()
                session.close()
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
