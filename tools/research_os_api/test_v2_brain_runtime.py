#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest

import test_v2_brain_context
import test_v2_brain_decision
import test_v2_skill_registry
from agent_platform import AgentRegistry
from v2_brain_core import ActivityLedger, WorkingMemory
from v2_brain_decision import ActionCandidate
from v2_brain_runtime import BrainRuntime
from v2_brain_team import BRAIN_TEAM_IDS


class BrainRuntimeTests(unittest.TestCase):
    def make_runtime(self, root: str) -> BrainRuntime:
        return BrainRuntime(
            registry=AgentRegistry(),
            working_memory=WorkingMemory(root),
            ledger=ActivityLedger(root),
        )

    def test_runtime_attaches_all_twelve_brain_agents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self.make_runtime(tmp)
            report = runtime.introspect()
            self.assertEqual(12, report["team"]["member_count"])
            self.assertTrue(report["team"]["minimum_satisfied"])
            registered = {item["agent_id"] for item in report["team"]["members"]}
            self.assertEqual(set(BRAIN_TEAM_IDS), registered)

    def test_developer_plan_can_resolve_brain_team_capabilities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self.make_runtime(tmp)
            result = runtime.plan(
                "debug code build test",
                session_id="developer-brain-team",
                context={"unknown": ["current failing evidence"]},
            )
            plan = result["plan"]
            matches = {item.capability: set(item.agents) for item in plan.capability_matches}
            self.assertIn("v2_developer_intelligence_engineer", matches["debug"])
            self.assertIn("v2_developer_intelligence_engineer", matches["build"])
            self.assertIn("v2_developer_intelligence_engineer", matches["test"])
            self.assertIn("v2_brain_architect", matches["architecture"])
            self.assertEqual(12, result["team"]["ready_count"])

    def test_phase_two_introspection_exposes_context_skills_and_decision_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = self.make_runtime(tmp).introspect()
            self.assertEqual("brain_core_phase_2", report["phase"])
            self.assertGreaterEqual(report["skills"]["ready_count"], 3)
            self.assertTrue(report["context"]["secret_redaction"])
            self.assertFalse(report["decision_policy"]["hidden_chain_of_thought"])
            self.assertEqual("disabled_until_permissioned_execution_port", report["tool_execution"])

    def test_plan_returns_context_snapshot_without_secret_leak(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self.make_runtime(tmp)
            result = runtime.plan(
                "research architecture",
                session_id="context-runtime",
                context={"api_key": "must-not-leak", "known": ["repository exists"]},
            )
            self.assertEqual("Research OS", result["context"]["values"]["system"])
            self.assertEqual("[REDACTED]", result["context"]["values"]["api_key"])
            self.assertNotIn("must-not-leak", repr(result["context"]))

    def test_foundational_verification_skill_is_discoverable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self.make_runtime(tmp)
            matches = runtime.discover_skills("verification")
            self.assertEqual(["brain.evidence-verification"], [item["skill_id"] for item in matches])

    def test_action_evaluation_requires_permission_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self.make_runtime(tmp)
            blocked = runtime.evaluate_action(
                (
                    ActionCandidate(
                        "write",
                        "Write source",
                        state_change=True,
                        required_permissions=("source.write",),
                        required_evidence=("diff",),
                    ),
                )
            )
            self.assertEqual("blocked", blocked["decision"])

            allowed = runtime.evaluate_action(
                (
                    ActionCandidate(
                        "write",
                        "Write source",
                        state_change=True,
                        required_permissions=("source.write",),
                        required_evidence=("diff",),
                    ),
                ),
                granted_permissions=("source.write",),
                evidence={"diff": "prepared"},
            )
            self.assertEqual("allowed", allowed["decision"])
            self.assertEqual("write", allowed["selected_action_id"])


def load_tests(loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None) -> unittest.TestSuite:
    """Keep Phase 2 tests inside the existing consolidated Agent Platform gate."""
    del pattern
    suite = unittest.TestSuite()
    suite.addTests(tests)
    suite.addTests(loader.loadTestsFromModule(test_v2_brain_context))
    suite.addTests(loader.loadTestsFromModule(test_v2_brain_decision))
    suite.addTests(loader.loadTestsFromModule(test_v2_skill_registry))
    return suite


if __name__ == "__main__":
    unittest.main()
