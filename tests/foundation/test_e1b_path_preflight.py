from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from path_bootstrap import ensure_backend_path


ensure_backend_path()

from app.foundation.context import (  # noqa: E402
    AuthenticationMethod,
    PrincipalContext,
    PrincipalType,
    ScopeContext,
)
from app.models.foundation_execution import WorkAttempt  # noqa: E402
from app.services.controlled_builtin_executor import (  # noqa: E402
    ControlledBuiltinRejected,
    preflight_controlled_builtin,
)
from support import phase2a_authority_database  # noqa: E402


def _scope(
    tenant_id: str = "ten_local",
    workspace_id: str = "wsp_personal",
) -> ScopeContext:
    principal = PrincipalContext(
        principal_id="wrapper",
        principal_type=PrincipalType.RUNTIME_WRAPPER,
        authentication_method=AuthenticationMethod.SERVICE_CREDENTIAL,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        permission_names=frozenset({"work_order.execute"}),
    )
    return ScopeContext(principal, tenant_id, workspace_id)


def _claimed_attempt(session: Session, work_order_id: str) -> WorkAttempt:
    attempt = WorkAttempt(
        attempt_id="att_preflight",
        tenant_id="ten_local",
        workspace_id="wsp_personal",
        scope_key="ten_local:wsp_personal",
        work_order_id=work_order_id,
        attempt_number=1,
        trigger_reason="approved_execution",
        state="claimed",
        row_version=2,
        runtime_adapter_id="builtin.vs001_echo_markdown",
        runtime_adapter_version=session.execute(
            __import__("sqlalchemy").text(
                "SELECT json_extract(config_json, '$.script_sha256')"
                " FROM runtime_registry"
                " WHERE runtime_id='builtin.vs001_echo_markdown'"
            )
        ).scalar_one(),
        runtime_config_snapshot_json=session.execute(
            __import__("sqlalchemy").text(
                "SELECT config_json FROM runtime_registry"
                " WHERE runtime_id='builtin.vs001_echo_markdown'"
            )
        ).scalar_one(),
        lease_owner="wrapper",
        lease_token_hash="sha256:" + ("a" * 64),
        lease_generation=1,
        allowed_read_refs_json='["scratch://input"]',
        allowed_write_refs_json='["scratch://output"]',
        created_by="wrapper",
    )
    session.add(attempt)
    session.commit()
    return attempt


class E1BPathPreflightTests(unittest.TestCase):
    def test_exact_hash_scope_and_scratch_contract_pass(self) -> None:
        with phase2a_authority_database() as (database, work_order_id):
            engine = create_engine(f"sqlite:///{database}")
            session = Session(engine)
            try:
                with tempfile.TemporaryDirectory() as temporary:
                    attempt = _claimed_attempt(session, work_order_id)
                    scratch = Path(temporary) / "attempt"
                    scratch.mkdir()
                    decision = preflight_controlled_builtin(
                        attempt,
                        _scope(),
                        scratch_root=scratch,
                        allowed_temp_root=Path(temporary),
                    )
                    self.assertEqual(attempt.attempt_id, decision.attempt_id)
                    self.assertTrue(decision.evidence_ref.startswith("preflight://"))
                    self.assertTrue(decision.decision_hash.startswith("sha256:"))
            finally:
                session.close()
                engine.dispose()

    def test_hash_scope_and_path_contract_mismatches_fail_closed(self) -> None:
        with phase2a_authority_database() as (database, work_order_id):
            engine = create_engine(f"sqlite:///{database}")
            session = Session(engine)
            try:
                with tempfile.TemporaryDirectory() as temporary:
                    attempt = _claimed_attempt(session, work_order_id)
                    cases = (
                        (
                            "builtin_script_hash_mismatch",
                            lambda: (
                                setattr(
                                    attempt,
                                    "runtime_adapter_version",
                                    "sha256:" + ("0" * 64),
                                ),
                                setattr(
                                    attempt,
                                    "runtime_config_snapshot_json",
                                    json.dumps(
                                        {
                                            "executor": "controlled_builtin",
                                            "script_sha256": (
                                                "sha256:" + ("0" * 64)
                                            ),
                                            "scratch_only": True,
                                        },
                                        sort_keys=True,
                                        separators=(",", ":"),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "preflight_scope_mismatch",
                            lambda: setattr(attempt, "tenant_id", "ten_other"),
                        ),
                        (
                            "preflight_path_contract_mismatch",
                            lambda: setattr(
                                attempt,
                                "allowed_write_refs_json",
                                json.dumps(["scratch://../private"]),
                            ),
                        ),
                    )
                    original = {
                        "runtime_adapter_version": attempt.runtime_adapter_version,
                        "runtime_config_snapshot_json": (
                            attempt.runtime_config_snapshot_json
                        ),
                        "tenant_id": attempt.tenant_id,
                        "allowed_write_refs_json": attempt.allowed_write_refs_json,
                    }
                    for expected, mutate in cases:
                        for field, value in original.items():
                            setattr(attempt, field, value)
                        mutate()
                        scratch = Path(temporary) / expected
                        scratch.mkdir()
                        with self.assertRaisesRegex(
                            ControlledBuiltinRejected,
                            expected,
                        ):
                            preflight_controlled_builtin(
                                attempt,
                                _scope(),
                                scratch_root=scratch,
                                allowed_temp_root=Path(temporary),
                            )
                    session.rollback()
            finally:
                session.close()
                engine.dispose()

    def test_nonempty_symlink_and_outside_scratch_are_rejected(self) -> None:
        with phase2a_authority_database() as (database, work_order_id):
            engine = create_engine(f"sqlite:///{database}")
            session = Session(engine)
            try:
                with tempfile.TemporaryDirectory() as temporary:
                    attempt = _claimed_attempt(session, work_order_id)
                    root = Path(temporary)

                    nonempty = root / "nonempty"
                    nonempty.mkdir()
                    (nonempty / "existing").write_text("x", encoding="utf-8")
                    with self.assertRaisesRegex(
                        ControlledBuiltinRejected,
                        "scratch_root_not_empty",
                    ):
                        preflight_controlled_builtin(
                            attempt,
                            _scope(),
                            scratch_root=nonempty,
                            allowed_temp_root=root,
                        )

                    real = root / "real"
                    real.mkdir()
                    symlink = root / "symlink"
                    symlink.symlink_to(real, target_is_directory=True)
                    with self.assertRaisesRegex(
                        ControlledBuiltinRejected,
                        "scratch_symlink_forbidden",
                    ):
                        preflight_controlled_builtin(
                            attempt,
                            _scope(),
                            scratch_root=symlink,
                            allowed_temp_root=root,
                        )

                    with tempfile.TemporaryDirectory() as outside:
                        with self.assertRaisesRegex(
                            ControlledBuiltinRejected,
                            "scratch_root_outside_allowed_root",
                        ):
                            preflight_controlled_builtin(
                                attempt,
                                _scope(),
                                scratch_root=Path(outside),
                                allowed_temp_root=root,
                            )
            finally:
                session.close()
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
