from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.platform_production_hardening import (
    prove_evidence_provenance,
    prove_failure_recovery,
    run_platform_hardening,
    validate_distribution_contract,
    validate_scale_contract,
)


class PlatformProductionHardeningTests(unittest.TestCase):
    def test_failure_recovery_matrix(self) -> None:
        self.assertEqual(prove_failure_recovery(), ())

    def test_evidence_provenance_and_project_isolation(self) -> None:
        self.assertEqual(prove_evidence_provenance(), ())

    def test_scale_contract(self) -> None:
        self.assertEqual(validate_scale_contract(Path(__file__).resolve().parents[1]), ())

    def test_distribution_contract(self) -> None:
        self.assertEqual(validate_distribution_contract(Path(__file__).resolve().parents[1]), ())

    def test_platform_hardening_summary(self) -> None:
        summary = run_platform_hardening(Path(__file__).resolve().parents[1])
        self.assertEqual(summary.scale, "PASS")
        self.assertEqual(summary.failure_recovery, "PASS")
        self.assertEqual(summary.evidence_provenance, "PASS")
        self.assertEqual(summary.distribution_contract, "PASS")
        self.assertEqual(summary.runtime_readiness, "PASS")
        self.assertEqual(summary.production_readiness, "PASS")


if __name__ == "__main__":
    unittest.main()
