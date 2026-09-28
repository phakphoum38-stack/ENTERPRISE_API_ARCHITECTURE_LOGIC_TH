from __future__ import annotations

import unittest

from .final_gate_evidence import (
    build_final_gate_evidence,
    validate_final_gate_evidence,
)


class FinalGateEvidenceTests(unittest.TestCase):
    def test_canonical_identity_binds_one_lineage(self) -> None:
        evidence = build_final_gate_evidence(
            workflow_id="wf-1",
            run_id="run-1",
            execution_id="exec-1",
            delivery_ids=("delivery-1",),
            resource_versions=("resource-1@2",),
            terminal_status="passed",
        )
        validate_final_gate_evidence(
            evidence,
            expected_workflow_id="wf-1",
            expected_run_id="run-1",
            expected_execution_id="exec-1",
        )
        self.assertEqual(len(evidence.canonical_sha256), 64)

    def test_identity_mismatch_fails_closed(self) -> None:
        evidence = build_final_gate_evidence(
            workflow_id="wf-1",
            run_id="run-1",
            execution_id="exec-1",
        )
        with self.assertRaises(ValueError):
            validate_final_gate_evidence(
                evidence,
                expected_workflow_id="wf-other",
                expected_run_id="run-1",
                expected_execution_id="exec-1",
            )
