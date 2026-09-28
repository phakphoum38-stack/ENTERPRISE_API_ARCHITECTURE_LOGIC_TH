from __future__ import annotations

import unittest

from .final_gate_evidence import build_final_gate_evidence
from .final_gate_validator import validate_final_gate


class FinalGateValidatorTests(unittest.TestCase):
    def test_single_gate_passes_complete_lineage(self) -> None:
        evidence = build_final_gate_evidence(
            workflow_id="wf",
            run_id="run",
            execution_id="exec",
            delivery_ids=("delivery",),
            resource_versions=("resource@2",),
            terminal_status="passed",
            extra={"gate": "research-os"},
        )
        result = validate_final_gate(
            evidence,
            expected_workflow_id="wf",
            expected_run_id="run",
            expected_execution_id="exec",
        )
        self.assertTrue(result.passed)
        self.assertEqual(result.reasons, ())

    def test_gate_fails_closed_on_missing_lineage(self) -> None:
        evidence = build_final_gate_evidence(
            workflow_id="wf",
            run_id="run",
            execution_id="exec",
            terminal_status="passed",
        )
        result = validate_final_gate(
            evidence,
            expected_workflow_id="wf",
            expected_run_id="run",
            expected_execution_id="exec",
        )
        self.assertFalse(result.passed)
        self.assertIn("delivery lineage is empty", result.reasons)
        self.assertIn("resource lineage is empty", result.reasons)
