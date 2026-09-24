"""Tests for Phase D parity validation with deterministic fault injection."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from tools import validate_phase_d_cross_surface_parity as validator
from tools.capability_delegation import CANONICAL_DELEGATIONS
from tools.control_center_capability_registry import CANONICAL_CAPABILITY_BINDINGS


class PhaseDCrossSurfaceParityTests(unittest.TestCase):
    def test_canonical_shapes_are_reconciled(self) -> None:
        self.assertEqual((), validator.validate())

    def test_assurance_cannot_become_executable(self) -> None:
        assurance = next(item for item in CANONICAL_DELEGATIONS if item.capability_id == "assurance")
        mutated = type(assurance)(
            assurance.capability_id,
            assurance.executor_ref,
            assurance.operations,
            True,
        )
        with patch.object(
            validator,
            "CANONICAL_DELEGATIONS",
            tuple(mutated if item.capability_id == "assurance" else item for item in CANONICAL_DELEGATIONS),
        ):
            self.assertIn("assurance must remain non-executable", validator.validate())

    def test_executor_family_mismatch_fails_closed(self) -> None:
        friend = next(item for item in CANONICAL_CAPABILITY_BINDINGS if item.capability_id == "friend")
        mutated = type(friend)(
            friend.capability_id,
            friend.domain,
            friend.label,
            friend.ui_ref,
            friend.contract_ref,
            "mismatched/runtime",
            "mismatched/executor",
            friend.observation_ref,
            friend.evidence_ref,
            friend.state_ref,
            friend.inspector_ref,
            friend.status,
            friend.notes,
        )
        with patch.object(
            validator,
            "CANONICAL_CAPABILITY_BINDINGS",
            tuple(mutated if item.capability_id == "friend" else item for item in CANONICAL_CAPABILITY_BINDINGS),
        ):
            self.assertIn("friend: registry executor family mismatch", validator.validate())

    def test_missing_final_gate_hook_fails_closed(self) -> None:
        with patch.object(validator, "_read_unified_final_gate", lambda root: ""):
            self.assertIn(
                "Unified Final Gate is missing the Phase D parity test",
                validator.validate(),
            )


if __name__ == "__main__":
    unittest.main()
