import tempfile
import unittest
from pathlib import Path

from tools.test_phase_d_cross_surface_parity import run_validation


class PhaseDCrossSurfaceParityTests(unittest.TestCase):
    def test_canonical_main_shapes_are_reconciled(self) -> None:
        self.assertEqual((), run_validation())

    def test_assurance_cannot_become_executable(self) -> None:
        errors = run_validation(assurance_execution_supported=True)
        self.assertIn("assurance must remain non-executable", errors)

    def test_executor_mismatch_fails_closed(self) -> None:
        errors = run_validation(executor_mismatch="friend")
        self.assertIn("friend: registry/delegation executor mismatch", errors)

    def test_missing_final_gate_hook_fails_closed(self) -> None:
        errors = run_validation(final_gate_hook=False)
        self.assertIn("Unified Final Gate is missing the Phase D parity test", errors)


if __name__ == "__main__":
    unittest.main()
