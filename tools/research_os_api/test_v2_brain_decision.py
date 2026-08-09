#!/usr/bin/env python3
from __future__ import annotations

import unittest

from v2_brain_decision import ActionCandidate, DecisionEngine


class BrainDecisionTests(unittest.TestCase):
    def test_read_only_local_action_is_low_risk_and_allowed(self) -> None:
        engine = DecisionEngine()
        result = engine.choose((ActionCandidate("inspect", "Inspect local state"),))
        self.assertEqual("inspect", result.selected_action_id)
        self.assertEqual("allowed", result.decision)
        self.assertEqual("low", result.risk.level)
        self.assertFalse(result.risk.approval_required)

    def test_missing_permission_blocks_action(self) -> None:
        engine = DecisionEngine()
        result = engine.choose(
            (
                ActionCandidate(
                    "write-source",
                    "Write source file",
                    state_change=True,
                    required_permissions=("source.write",),
                ),
            ),
            granted_permissions=(),
        )
        self.assertIsNone(result.selected_action_id)
        self.assertEqual("blocked", result.decision)
        self.assertIn("permission missing: source.write", result.alternatives[0]["risk"]["blocked_reasons"])

    def test_release_production_action_requires_approval_when_gates_are_present(self) -> None:
        engine = DecisionEngine()
        result = engine.choose(
            (
                ActionCandidate(
                    "deploy",
                    "Deploy verified candidate",
                    state_change=True,
                    network=True,
                    release_boundary=True,
                    production_boundary=True,
                    required_permissions=("production.deploy",),
                    required_evidence=("exact_sha", "verified_artifact"),
                ),
            ),
            granted_permissions=("production.deploy",),
            evidence={"exact_sha": "abc", "verified_artifact": "artifact-1"},
        )
        self.assertEqual("deploy", result.selected_action_id)
        self.assertEqual("approval_required", result.decision)
        self.assertEqual("critical", result.risk.level)
        self.assertTrue(result.risk.approval_required)

    def test_missing_evidence_blocks_even_when_permission_exists(self) -> None:
        engine = DecisionEngine()
        risk = engine.assess(
            ActionCandidate(
                "candidate",
                "Promote candidate",
                state_change=True,
                required_permissions=("release.write",),
                required_evidence=("exact_sha",),
            ),
            granted_permissions=("release.write",),
            evidence={},
        )
        self.assertTrue(risk.blocked)
        self.assertEqual(("evidence missing: exact_sha",), risk.blocked_reasons)

    def test_lower_risk_beats_higher_utility(self) -> None:
        engine = DecisionEngine()
        result = engine.choose(
            (
                ActionCandidate("safe", "Read evidence", utility=1),
                ActionCandidate("risky", "Network mutation", state_change=True, network=True, utility=99),
            )
        )
        self.assertEqual("safe", result.selected_action_id)

    def test_policy_is_explicit_and_does_not_expose_hidden_reasoning(self) -> None:
        policy = DecisionEngine.policy()
        self.assertFalse(policy["hidden_chain_of_thought"])
        self.assertIn("lowest_risk", policy["selection_order"])


if __name__ == "__main__":
    unittest.main()
