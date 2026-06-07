from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import unittest

from path_bootstrap import ensure_backend_path

ensure_backend_path()

from app.models.canonical_work_order import CanonicalWorkOrder
from app.services.canonical_work_order_read_service import (
    MODE_B_CLASSIFICATION,
    PROVENANCE_KEYS,
    project_canonical,
    project_legacy,
)
from support import REPO_ROOT


RT3_HASH = "sha256:7ff77d02857af95748b59dd96a50ef2c0950d4c8f6b21fb086927fff2d192985"
RT4_HASH = "sha256:6cf162614b5aa99097c58ccf9803085ea25ab4716f2f6a34409891ff4f2a362b"


def _legacy_snapshot(work_order_id: str) -> dict:
    return {
        "work_order_id": work_order_id,
        "skill_id": "legacy-skill",
        "task_type": "legacy-task",
        "input_context": "legacy input",
        "expected_output": "legacy output",
        "status": "completed",
        "created_at": "2026-05-29 04:46:03",
        "completed_at": "2026-05-29 04:46:11",
        "attempt_count": 1,
    }


def _rt3(row: dict, *, authority: str, resolution_status: str) -> dict:
    return {
        "classification": row["classification"],
        "evidence_tier": row["evidence_tier"],
        "reason_codes": row["reason_codes"],
        "recommended_disposition": row["recommended_disposition"],
        "source_system": row["source_system"],
        "source_id": row["source_id"],
        "authority": authority,
        "resolution_status": resolution_status,
    }


def _rt4(mapping: dict, anomaly_ids: list[str]) -> dict:
    return {
        "source_hash": mapping["source_hash"],
        "source_key": mapping["source_key"],
        "anomaly_refs": anomaly_ids,
        "mapping_rule": mapping["mapping_rule"],
        "migration_batch_id": mapping["migration_batch_id"],
        "evidence_refs": [
            {"type": "rt3_classification", "hash": RT3_HASH},
            {"type": "rt4_dry_run_plan", "hash": RT4_HASH},
        ],
    }


class E1AProvenanceProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rt3_report = json.loads(
            (REPO_ROOT / "reports/migration/v0.47-F0-C2-classification.json").read_text()
        )
        cls.rt4_report = json.loads(
            (REPO_ROOT / "reports/migration/v0.47-F0-C3-backfill-dry-run.json").read_text()
        )

    def _evidence(self, classification: str):
        matching_rows = [
            row
            for row in self.rt3_report["systems"]["work_orders"]
            if row["classification"] == classification
        ]
        rt3_row = dict(
            matching_rows[0]
            if matching_rows
            else self.rt3_report["systems"]["work_orders"][0]
        )
        if not matching_rows:
            rt3_row["classification"] = classification
            rt3_row["evidence_tier"] = "D"
            rt3_row["reason_codes"] = [f"fixture_{classification}"]
        mapping = next(
            row
            for row in self.rt4_report["work_order_mappings"]
            if row["source_key"] == rt3_row["source_id"]
        )
        anomalies = [
            row["anomaly_id"]
            for row in self.rt4_report["reconciliation_anomalies"]
            if row["source_key"] == rt3_row["source_id"]
        ]
        return rt3_row, mapping, anomalies

    def test_canonical_fixture_requires_scope_state_and_version(self) -> None:
        work_order = CanonicalWorkOrder(
            work_order_id="wo_canonical",
            tenant_id="ten_local",
            workspace_id="wsp_personal",
            skill_id="skill",
            task_type="task",
            input_context="input",
            expected_output="output",
            status="created",
            canonical_state="draft",
            row_version=1,
            created_at=datetime(2026, 6, 7),
        )
        envelope = project_canonical(work_order, source_hash="sha256:fixture")
        self.assertEqual(
            {"data", "provenance", "tenant_id", "workspace_id"},
            set(envelope),
        )
        self.assertEqual(PROVENANCE_KEYS, frozenset(envelope["provenance"]))
        self.assertEqual("canonical", envelope["provenance"]["authority"])
        self.assertEqual("draft", envelope["data"]["canonical_state"])

        work_order.canonical_state = None
        with self.assertRaisesRegex(
            ValueError,
            "canonical_projection_requires_resolved_record",
        ):
            project_canonical(work_order, source_hash="sha256:fixture")

    def test_legacy_projection_uses_explicit_three_part_evidence(self) -> None:
        rt3_row, mapping, anomalies = self._evidence("noncanonical_history")
        authority, resolution = MODE_B_CLASSIFICATION["noncanonical_history"]
        envelope = project_legacy(
            _legacy_snapshot(rt3_row["source_id"]),
            _rt3(rt3_row, authority=authority, resolution_status=resolution),
            _rt4(mapping, anomalies),
        )
        self.assertIsNone(envelope["tenant_id"])
        self.assertIsNone(envelope["workspace_id"])
        self.assertIsNone(envelope["data"]["canonical_state"])
        self.assertEqual("completed", envelope["data"]["legacy_status"])
        self.assertEqual("legacy_only", envelope["provenance"]["authority"])
        self.assertEqual("work_orders", envelope["provenance"]["source_system"])
        self.assertEqual(anomalies, envelope["provenance"]["anomaly_refs"])
        self.assertEqual(PROVENANCE_KEYS, frozenset(envelope["provenance"]))

    def test_mode_b_requires_explicit_valid_authority_and_resolution(self) -> None:
        rt3_row, mapping, anomalies = self._evidence("noncanonical_history")
        evidence = _rt3(
            rt3_row,
            authority="legacy_only",
            resolution_status="unresolved",
        )
        for missing in ("authority", "resolution_status"):
            invalid = dict(evidence)
            invalid.pop(missing)
            with self.subTest(missing=missing):
                with self.assertRaisesRegex(
                    ValueError,
                    "invalid_mode_b_rt3_evidence",
                ):
                    project_legacy(
                        _legacy_snapshot(rt3_row["source_id"]),
                        invalid,
                        _rt4(mapping, anomalies),
                    )
        invalid = dict(evidence, authority="canonical")
        with self.assertRaisesRegex(ValueError, "invalid_mode_b_rt3_evidence"):
            project_legacy(
                _legacy_snapshot(rt3_row["source_id"]),
                invalid,
                _rt4(mapping, anomalies),
            )

    def test_all_mode_b_classification_mappings_are_accepted(self) -> None:
        for classification, (authority, resolution) in MODE_B_CLASSIFICATION.items():
            with self.subTest(classification=classification):
                rt3_row, mapping, anomalies = self._evidence(classification)
                envelope = project_legacy(
                    _legacy_snapshot(rt3_row["source_id"]),
                    _rt3(
                        rt3_row,
                        authority=authority,
                        resolution_status=resolution,
                    ),
                    _rt4(mapping, anomalies),
                )
                self.assertEqual(authority, envelope["provenance"]["authority"])
                self.assertEqual(
                    resolution,
                    envelope["provenance"]["resolution_status"],
                )

    def test_source_mismatch_is_not_merged(self) -> None:
        rt3_row, mapping, anomalies = self._evidence("conflicting")
        authority, resolution = MODE_B_CLASSIFICATION["conflicting"]
        with self.assertRaisesRegex(ValueError, "legacy_projection_source_mismatch"):
            project_legacy(
                _legacy_snapshot("different-id"),
                _rt3(
                    rt3_row,
                    authority=authority,
                    resolution_status=resolution,
                ),
                _rt4(mapping, anomalies),
            )


if __name__ == "__main__":
    unittest.main()
