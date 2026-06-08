from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

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
    execute_controlled_builtin,
    preflight_controlled_builtin,
)
from support import phase2a_authority_database  # noqa: E402


def _scope() -> ScopeContext:
    principal = PrincipalContext(
        principal_id="wrapper",
        principal_type=PrincipalType.RUNTIME_WRAPPER,
        authentication_method=AuthenticationMethod.SERVICE_CREDENTIAL,
        tenant_id="ten_local",
        workspace_id="wsp_personal",
        permission_names=frozenset({"work_order.execute"}),
    )
    return ScopeContext(principal, "ten_local", "wsp_personal")


def _attempt(session: Session, work_order_id: str) -> WorkAttempt:
    config = session.execute(
        __import__("sqlalchemy").text(
            "SELECT config_json FROM runtime_registry"
            " WHERE runtime_id='builtin.vs001_echo_markdown'"
        )
    ).scalar_one()
    version = __import__("json").loads(config)["script_sha256"]
    attempt = WorkAttempt(
        attempt_id="att_executor",
        tenant_id="ten_local",
        workspace_id="wsp_personal",
        scope_key="ten_local:wsp_personal",
        work_order_id=work_order_id,
        attempt_number=1,
        trigger_reason="approved_execution",
        state="claimed",
        row_version=2,
        runtime_adapter_id="builtin.vs001_echo_markdown",
        runtime_adapter_version=version,
        runtime_config_snapshot_json=config,
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


class E1BControlledBuiltinExecutorTests(unittest.TestCase):
    def test_fixed_builtin_captures_bounded_evidence_in_scratch(self) -> None:
        with phase2a_authority_database() as (database, work_order_id):
            engine = create_engine(f"sqlite:///{database}")
            session = Session(engine)
            try:
                with tempfile.TemporaryDirectory() as temporary:
                    attempt = _attempt(session, work_order_id)
                    scratch = Path(temporary) / "attempt"
                    scratch.mkdir()
                    decision = preflight_controlled_builtin(
                        attempt,
                        _scope(),
                        scratch_root=scratch,
                        allowed_temp_root=Path(temporary),
                    )
                    session.close()
                    run = execute_controlled_builtin(
                        decision,
                        {"heading": "Truthful execution", "body": "Evidence first."},
                    )

                    self.assertEqual("succeeded", run.evidence.terminal_state)
                    self.assertEqual(0, run.evidence.exit_code)
                    self.assertEqual(decision.evidence_ref, run.preflight_ref)
                    self.assertEqual(
                        "# Truthful execution\n\nEvidence first.\n",
                        (scratch / "output/result.md").read_text(encoding="utf-8"),
                    )
                    self.assertEqual(
                        "controlled_builtin_completed:result.md\n",
                        (scratch / "output/stdout.txt").read_text(encoding="utf-8"),
                    )
                    self.assertEqual(
                        "",
                        (scratch / "output/stderr.txt").read_text(encoding="utf-8"),
                    )
                    self.assertEqual(
                        {
                            "input/input.json",
                            "output/result.md",
                            "output/stderr.txt",
                            "output/stdout.txt",
                        },
                        {
                            path.relative_to(scratch).as_posix()
                            for path in scratch.rglob("*")
                            if path.is_file()
                        },
                    )
            finally:
                if session.is_active:
                    session.close()
                engine.dispose()

    def test_tampered_preflight_and_timeout_fail_closed_with_evidence(self) -> None:
        with phase2a_authority_database() as (database, work_order_id):
            engine = create_engine(f"sqlite:///{database}")
            session = Session(engine)
            try:
                with tempfile.TemporaryDirectory() as temporary:
                    attempt = _attempt(session, work_order_id)
                    root = Path(temporary)
                    scratch = root / "tampered"
                    scratch.mkdir()
                    decision = preflight_controlled_builtin(
                        attempt,
                        _scope(),
                        scratch_root=scratch,
                        allowed_temp_root=root,
                    )
                    object.__setattr__(
                        decision,
                        "decision_hash",
                        "sha256:" + ("0" * 64),
                    )
                    with self.assertRaisesRegex(
                        ControlledBuiltinRejected,
                        "preflight_decision_hash_mismatch",
                    ):
                        execute_controlled_builtin(
                            decision,
                            {"heading": "x", "body": "y"},
                        )

                    timeout_scratch = root / "timeout"
                    timeout_scratch.mkdir()
                    timeout_decision = preflight_controlled_builtin(
                        attempt,
                        _scope(),
                        scratch_root=timeout_scratch,
                        allowed_temp_root=root,
                    )
                    with mock.patch(
                        "app.services.controlled_builtin_executor.subprocess.run",
                        side_effect=subprocess.TimeoutExpired(
                            cmd=["builtin"],
                            timeout=0.001,
                        ),
                    ):
                        timed_out = execute_controlled_builtin(
                            timeout_decision,
                            {"heading": "x", "body": "y"},
                            timeout_seconds=0.001,
                        )
                    self.assertEqual("failed", timed_out.evidence.terminal_state)
                    self.assertEqual(124, timed_out.evidence.exit_code)
                    self.assertEqual(
                        "controlled_builtin_timeout",
                        timed_out.evidence.error_code,
                    )
                    self.assertTrue(
                        (timeout_scratch / "output/result.md").is_file()
                    )
            finally:
                session.close()
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
