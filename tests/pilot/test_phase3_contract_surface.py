from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class Phase3ContractSurfaceTests(unittest.TestCase):
    def test_execution_service_seven_command_signatures_remain_present(self) -> None:
        tree = ast.parse(
            (
                ROOT / "backend/app/services/canonical_execution_service.py"
            ).read_text(encoding="utf-8")
        )
        functions = {
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        self.assertTrue(
            {
                "request_execution_approval",
                "decide_execution_approval",
                "allocate_execution_attempt",
                "claim_execution_attempt",
                "record_invocation_started",
                "ingest_attempt_result",
                "decide_execution_review",
            }.issubset(functions)
        )

    def test_command_repository_keeps_private_cas_and_named_commands(self) -> None:
        tree = ast.parse(
            (
                ROOT / "backend/app/repositories/canonical_work_order_command.py"
            ).read_text(encoding="utf-8")
        )
        repository = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "CanonicalWorkOrderCommandRepository"
        )
        methods = {
            node.name
            for node in repository.body
            if isinstance(node, ast.FunctionDef)
        }
        self.assertIn("_compare_and_set_state", methods)
        self.assertNotIn("compare_and_set_state", methods)
        self.assertTrue(
            {
                "create_draft",
                "request_approval",
                "apply_approval_decision",
                "mark_running_after_claim",
                "mark_waiting_review_after_result",
                "apply_review_outcome",
            }.issubset(methods)
        )

    def test_pilot_package_does_not_import_forbidden_startup_paths(self) -> None:
        forbidden = {
            "app.main",
            "app.database",
            "app.runtime.seed_runtimes",
        }
        for path in (ROOT / "backend/app/pilot").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module)
                elif isinstance(node, ast.Import):
                    imports.update(alias.name for alias in node.names)
            self.assertEqual(set(), forbidden.intersection(imports), path.name)


if __name__ == "__main__":
    unittest.main()
