#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest

import test_v2_brain_context
import test_v2_brain_decision
import test_v2_domain_skills
import test_v2_execution_controller
import test_v2_execution_hardening
import test_v2_governed_task_runner
import test_v2_learning_engine
import test_v2_secret_redactor
import test_v2_skill_executor
import test_v2_skill_registry
import test_v2_tool_registry
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

    def test_runtime_introspection_exposes_complete_brain_layers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = self.make_runtime(tmp).introspect()
            self.assertEqual("brain_core_phase_10", report["phase"])
            self.assertEqual("brain_core_phase_8", report["task_runner_phase"])
            self.assertEqual("brain_core_phase_9", report["learning_phase"])
            self.assertEqual("brain_core_phase_10", report["domain_skills_phase"])
            self.assertGreaterEqual(report["skills"]["ready_count"], 30)
            self.assertGreaterEqual(report["skills"]["operational_contract_count"], 30)
            self.assertEqual(3, report["tools"]["ready_count"])
            self.assertTrue(report["context"]["secret_redaction"])
            self.assertFalse(report["decision_policy"]["hidden_chain_of_thought"])
            self.assertEqual("secret_aware_permissioned_controller_enabled", report["tool_execution"])
            self.assertFalse(report["direct_adapter_access"])
            self.assertEqual("explicit_approval", report["execution"]["write_policy"])
            self.assertTrue(report["secret_redaction"]["value_aware"])
            self.assertTrue(report["post_execution_verification"])
            self.assertEqual("brain-skill-tool-execution-phase-4", report["skill_execution"]["contract"])
            self.assertEqual("brain-governed-task-runner-phase-8", report["task_runner"]["contract"])
            self.assertEqual("brain-learning-experience-phase-9", report["learning"]["contract"])
            self.assertEqual("brain-domain-skills-phase-10", report["domain_skills"]["contract"])
            self.assertEqual("AgentOrchestrator", report["canonical_dependency_graph"])
            self.assertFalse(report["task_runner"]["unrestricted_shell"])
            self.assertFalse(report["self_modification"])
            self.assertFalse(report["learning"]["policy"]["automatic_skill_rewrite"])

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

    def test_foundational_and_domain_verification_skills_are_discoverable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self.make_runtime(tmp)
            matches = runtime.discover_skills("verification")
            ids = {item["skill_id"] for item in matches}
            self.assertIn("brain.evidence-verification", ids)
            self.assertIn("software.regression-verification", ids)
            self.assertIn("security.permission-review", ids)

    def test_domain_skill_exposes_operational_procedure_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self.make_runtime(tmp)
            core = runtime.skills.describe("brain.goal-analysis")
            domain = runtime.skills.describe("software.debug-diagnosis")
            self.assertTrue(core["operational_contract"])
            self.assertTrue(core["procedure"])
            self.assertTrue(domain["operational_contract"])
            self.assertTrue(domain["required_evidence"])

    def test_internal_skill_tool_runs_only_with_required_permission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self.make_runtime(tmp)
            blocked = runtime.execute_tool(
                "brain.skills.inspect",
                "list",
                session_id="tool-runtime",
            )
            self.assertEqual("blocked", blocked["status"])

            completed = runtime.execute_tool(
                "brain.skills.inspect",
                "list",
                session_id="tool-runtime",
                granted_permissions=("runtime.read",),
                idempotency_key="skills-list-once",
            )
            self.assertEqual("completed", completed["status"])
            self.assertGreaterEqual(completed["output"]["count"], 30)
            self.assertEqual(1, completed["attempts"])

    def test_context_tool_routes_through_hardened_execution_controller(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self.make_runtime(tmp)
            completed = runtime.execute_tool(
                "brain.context.inspect",
                "build",
                session_id="context-tool",
                payload={
                    "objective": "inspect architecture",
                    "context": {"api_key": "do-not-expose"},
                },
                granted_permissions=("runtime.read",),
            )
            self.assertEqual("completed", completed["status"])
            self.assertNotIn("do-not-expose", repr(completed))
            self.assertEqual("[REDACTED]", completed["output"]["values"]["api_key"])

    def test_core_goal_analysis_skill_matches_context_tool_and_verifies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self.make_runtime(tmp)
            match = runtime.match_tools(("context_engine",))
            self.assertTrue(match["matched"])
            self.assertEqual("brain.context.inspect", match["selected_tool_id"])

            result = runtime.execute_skill(
                "brain.goal-analysis",
                "build",
                session_id="goal-skill",
                payload={"objective": "understand Research OS architecture"},
                granted_permissions=("memory.read", "runtime.read"),
            )
            self.assertEqual("verified", result["status"])
            self.assertEqual("brain.context.inspect", result["selected_tool_id"])
            self.assertTrue(result["verification"]["verified"])

    def test_runtime_secret_values_do_not_escape_tool_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self.make_runtime(tmp)
            secret = "runtime-explicit-secret-123456789"
            result = runtime.execute_tool(
                "brain.context.inspect",
                "build",
                session_id="runtime-secret",
                payload={
                    "objective": "inspect secret handling",
                    "context": {"note": f"contains {secret}"},
                },
                granted_permissions=("runtime.read",),
                secret_values=(secret,),
            )
            self.assertEqual("completed", result["status"])
            self.assertNotIn(secret, repr(result))
            self.assertIn("[REDACTED]", repr(result))

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
    """Keep Brain phase suites inside the existing consolidated Agent Platform gate."""
    del pattern
    suite = unittest.TestSuite()
    suite.addTests(tests)
    suite.addTests(loader.loadTestsFromModule(test_v2_brain_context))
    suite.addTests(loader.loadTestsFromModule(test_v2_brain_decision))
    suite.addTests(loader.loadTestsFromModule(test_v2_skill_registry))
    suite.addTests(loader.loadTestsFromModule(test_v2_domain_skills))
    suite.addTests(loader.loadTestsFromModule(test_v2_tool_registry))
    suite.addTests(loader.loadTestsFromModule(test_v2_execution_controller))
    suite.addTests(loader.loadTestsFromModule(test_v2_secret_redactor))
    suite.addTests(loader.loadTestsFromModule(test_v2_execution_hardening))
    suite.addTests(loader.loadTestsFromModule(test_v2_skill_executor))
    suite.addTests(loader.loadTestsFromModule(test_v2_governed_task_runner))
    suite.addTests(loader.loadTestsFromModule(test_v2_learning_engine))
    return suite


if __name__ == "__main__":
    unittest.main()
