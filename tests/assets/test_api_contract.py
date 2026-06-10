from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class Vs002ApiContractTests(unittest.TestCase):
    def test_pilot_routes_delegate_only_to_gateway(self) -> None:
        source = (ROOT / "backend/app/pilot/app.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        self.assertIn("app.pilot.gateway", imports)
        self.assertNotIn("app.services.pilot_asset_service", imports)
        self.assertNotIn("app.repositories.pilot_asset", imports)
        for route in (
            '"/api/v1/vs001/assets"',
            '"/api/v1/vs001/assets/{asset_id}"',
            '"/api/v1/vs001/assets/{asset_id}/content"',
            '"/api/v1/vs001/assets/{asset_id}/approve"',
        ):
            self.assertIn(route, source)

    def test_frontend_has_separate_review_and_asset_approval_surfaces(self) -> None:
        work_order_page = (
            ROOT / "frontend/src/app/vs001/page.tsx"
        ).read_text(encoding="utf-8")
        asset_page = (
            ROOT / "frontend/src/app/vs001/assets/[asset_id]/page.tsx"
        ).read_text(encoding="utf-8")
        self.assertIn("4. Review Passed", work_order_page)
        self.assertIn("Approve Asset Candidate", asset_page)
        self.assertIn("Not Public-safe", asset_page)
        self.assertNotIn("Auto-Approve", work_order_page + asset_page)

    def test_public_contract_excludes_storage_and_scratch_paths(self) -> None:
        gateway = (
            ROOT / "backend/app/pilot/gateway.py"
        ).read_text(encoding="utf-8")
        types = (ROOT / "frontend/src/types/vs001.ts").read_text(
            encoding="utf-8"
        )
        self.assertNotIn('"scratch_root": receipt.scratch_root', gateway)
        self.assertNotIn('"result_ref": attempt.result_ref', gateway)
        self.assertNotIn("scratch_root:", types)
        self.assertNotIn("result_ref:", types)
        self.assertNotIn("storage_ref:", types)


if __name__ == "__main__":
    unittest.main()
