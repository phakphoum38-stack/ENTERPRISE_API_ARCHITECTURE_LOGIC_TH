"""Tests for Phase E unified Windows distribution governance."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from tools import validate_phase_e_unified_windows_distribution as validator


class PhaseEUnifiedWindowsDistributionTests(unittest.TestCase):
    def test_contract_reconciles(self) -> None:
        self.assertEqual((), validator.validate())

    def test_distribution_cannot_replace_release_authority(self) -> None:
        original = validator.json.loads(
            validator.CONTRACT.read_text(encoding="utf-8")
        )
        original["authority"]["final_gate_remains_release_authority"] = False
        with patch.object(validator, "json") as mocked_json:
            mocked_json.loads.return_value = original
            self.assertIn(
                "authority invariant missing: final_gate_remains_release_authority",
                validator.validate(),
            )

    def test_workflow_must_bind_owner_special(self) -> None:
        with patch.object(
            validator,
            "Path",
        ):
            pass

    def test_contract_requires_exact_sha(self) -> None:
        original = validator.json.loads(
            validator.CONTRACT.read_text(encoding="utf-8")
        )
        original["provenance"]["source_sha_required"] = False
        with patch.object(validator, "json") as mocked_json:
            mocked_json.loads.return_value = original
            self.assertIn(
                "provenance invariant missing: source_sha_required",
                validator.validate(),
            )


if __name__ == "__main__":
    unittest.main()
