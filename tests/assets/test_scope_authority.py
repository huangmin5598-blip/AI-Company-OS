from __future__ import annotations

import unittest

from path_bootstrap import ensure_backend_path
from test_vuo import PilotAssetScenario


ensure_backend_path()

from app.foundation.context import (  # noqa: E402
    AuthenticationMethod,
    PrincipalContext,
    PrincipalType,
    RequestContext,
    RequestOrigin,
    ScopeContext,
)
from app.repositories.pilot_asset import PilotAssetRepository  # noqa: E402
from app.services.pilot_asset_service import approve_asset_candidate  # noqa: E402
from app.models.pilot_asset import PilotAssetBase  # noqa: E402
from app.models.foundation_base import FoundationBase  # noqa: E402
from app.models.base import Base  # noqa: E402


class Vs002ScopeAuthorityTests(unittest.TestCase):
    def test_pilot_asset_metadata_is_isolated(self) -> None:
        self.assertIsNot(PilotAssetBase.metadata, FoundationBase.metadata)
        self.assertIsNot(PilotAssetBase.metadata, Base.metadata)
        self.assertNotIn("pilot_assets", FoundationBase.metadata.tables)
        self.assertNotIn("pilot_assets", Base.metadata.tables)

    def test_cross_tenant_asset_lookup_is_non_disclosing(self) -> None:
        scenario = PilotAssetScenario()
        try:
            _work_order_id, _executed, reviewed = scenario.candidate()
            asset_id = reviewed["assets"][0]["asset_id"]
            principal = PrincipalContext(
                principal_id="other",
                principal_type=PrincipalType.HUMAN,
                authentication_method=AuthenticationMethod.SESSION,
                tenant_id="ten_other",
                workspace_id="wsp_other",
                permission_names=frozenset({"asset.read"}),
            )
            scope = ScopeContext(principal, "ten_other", "wsp_other")
            with scenario.database.command_session() as session:
                self.assertIsNone(
                    PilotAssetRepository(session).get_by_id(scope, asset_id)
                )
        finally:
            scenario.close()

    def test_runtime_wrapper_cannot_approve_asset(self) -> None:
        scenario = PilotAssetScenario()
        try:
            _work_order_id, _executed, reviewed = scenario.candidate()
            asset_id = reviewed["assets"][0]["asset_id"]
            candidate = scenario.gateway.get_asset(
                scenario.request("wrapper-target"),
                asset_id,
            )
            approval = candidate["approval"]
            founder = scenario.request("wrapper-approval")
            wrapper_principal = PrincipalContext(
                principal_id="runtime-wrapper:test",
                principal_type=PrincipalType.RUNTIME_WRAPPER,
                authentication_method=AuthenticationMethod.SERVICE_CREDENTIAL,
                tenant_id=founder.scope.tenant_id,
                workspace_id=founder.scope.workspace_id,
                permission_names=frozenset(
                    {"asset.read", "asset.promote", "approval.decide"}
                ),
            )
            wrapper = RequestContext(
                scope=ScopeContext(
                    wrapper_principal,
                    founder.scope.tenant_id,
                    founder.scope.workspace_id,
                ),
                origin=RequestOrigin.INTERNAL_WORKER,
                idempotency_key="runtime-wrapper-asset-approval",
                mode=founder.mode,
            )
            with scenario.database.command_session() as session:
                with self.assertRaisesRegex(
                    PermissionError,
                    "runtime_wrapper_cannot_approve_asset",
                ):
                    approve_asset_candidate(
                        session,
                        wrapper,
                        asset_id=asset_id,
                        approval_id=approval["approval_id"],
                        expected_asset_version=1,
                        expected_approval_version=1,
                    )
        finally:
            scenario.close()

    def test_non_founder_human_cannot_bypass_gateway_asset_approval(self) -> None:
        scenario = PilotAssetScenario()
        try:
            _work_order_id, _executed, reviewed = scenario.candidate()
            asset_id = reviewed["assets"][0]["asset_id"]
            candidate = scenario.gateway.get_asset(
                scenario.request("human-bypass-target"),
                asset_id,
            )
            founder = scenario.request("human-bypass-founder")
            other_principal = PrincipalContext(
                principal_id="reviewer-other",
                principal_type=PrincipalType.HUMAN,
                authentication_method=AuthenticationMethod.SESSION,
                tenant_id=founder.scope.tenant_id,
                workspace_id=founder.scope.workspace_id,
                permission_names=frozenset(
                    {"asset.read", "asset.promote", "approval.decide"}
                ),
                local_mode=False,
            )
            other = RequestContext(
                scope=ScopeContext(
                    other_principal,
                    founder.scope.tenant_id,
                    founder.scope.workspace_id,
                ),
                origin=RequestOrigin.API,
                idempotency_key="human-bypass-asset-approval",
                mode=founder.mode,
            )
            with scenario.database.command_session() as session:
                with self.assertRaisesRegex(
                    PermissionError,
                    "pilot_single_actor_asset_approval_exception_not_applicable",
                ):
                    approve_asset_candidate(
                        session,
                        other,
                        asset_id=asset_id,
                        approval_id=candidate["approval"]["approval_id"],
                        expected_asset_version=1,
                        expected_approval_version=1,
                    )
        finally:
            scenario.close()

    def test_asset_authority_fields_cannot_be_promoted_or_published(self) -> None:
        scenario = PilotAssetScenario()
        try:
            _work_order_id, _executed, reviewed = scenario.candidate()
            asset = scenario.gateway.get_asset(
                scenario.request("authority-read"),
                reviewed["assets"][0]["asset_id"],
            )
            self.assertEqual("pilot_non_authoritative", asset["asset"]["authority"])
            self.assertEqual("restricted", asset["asset"]["visibility"])
            self.assertIsNone(asset["asset"]["public_safe_ref"])
            self.assertFalse(asset["governance"]["public_safe"])
            self.assertFalse(asset["governance"]["official_asset_center"])
        finally:
            scenario.close()


if __name__ == "__main__":
    unittest.main()
