#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_platform import AgentRegistry
from v2_brain_core import ActivityLedger, ResearchOSBrain, WorkingMemory


class BrainCoreTests(unittest.TestCase):
    def make_brain(self, root: str) -> ResearchOSBrain:
        return ResearchOSBrain(
            registry=AgentRegistry(),
            working_memory=WorkingMemory(root),
            ledger=ActivityLedger(root),
        )

    def test_introspection_exposes_model_independent_control_plane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = self.make_brain(tmp)
            report = brain.introspect()
            self.assertEqual("Research OS", report["identity"]["system"])
            self.assertEqual("AI Brain Core", report["identity"]["component"])
            self.assertEqual("0.2.0", report["identity"]["version"])
            self.assertFalse(report["execution"]["direct_tool_execution"])
            ports = {item["name"]: item["state"] for item in report["ports"]}
            self.assertEqual("connected", ports["agent_registry"])
            self.assertEqual("connected_via_runtime", ports["skill_registry"])
            self.assertEqual("connected_via_runtime", ports["context_engine"])
            self.assertEqual("connected_via_runtime", ports["decision_engine"])
            self.assertEqual("port_ready", ports["tool_registry"])
            self.assertIn("debug", report["capabilities"])
            self.assertIn("developer", report["capabilities"]["debug"])

    def test_plan_detects_intent_and_resolves_existing_agent_capabilities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = self.make_brain(tmp)
            plan = brain.plan(
                "debug GitHub CI build and test failure",
                session_id="session-ci",
                context={
                    "known": ["repository is available"],
                    "unknown": ["failing step log"],
                    "constraints": ["do not guess the failure"],
                },
            )
            self.assertTrue(plan.executable, plan.blocked_reasons)
            self.assertIn("debug", plan.goal.intent)
            self.assertIn("github", plan.goal.intent)
            self.assertIn("build", plan.goal.intent)
            self.assertIn("test", plan.goal.intent)
            self.assertIn("gather_evidence", [step.step_id for step in plan.steps])
            matches = {item.capability: item for item in plan.capability_matches}
            self.assertIn("developer", matches["debug"].agents)
            self.assertIn("github", matches["workflow"].agents)

    def test_unknown_capability_blocks_execution_instead_of_guessing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = self.make_brain(tmp)
            original = brain._required_capabilities
            try:
                brain._required_capabilities = lambda _: ("capability-that-does-not-exist",)  # type: ignore[method-assign]
                plan = brain.plan("do a new unsupported task", session_id="blocked")
            finally:
                brain._required_capabilities = original  # type: ignore[method-assign]
            self.assertFalse(plan.executable)
            self.assertEqual(
                ("capability unavailable: capability-that-does-not-exist",),
                plan.blocked_reasons,
            )

    def test_working_memory_survives_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = self.make_brain(tmp)
            first.plan("research architecture", session_id="persisted")
            second = self.make_brain(tmp)
            state = second.session("persisted")["working_memory"]
            self.assertEqual("planned", state["status"])
            self.assertEqual("research architecture", state["current_goal"]["objective"])

    def test_activity_ledger_and_memory_redact_sensitive_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = self.make_brain(tmp)
            brain.plan(
                "research provider configuration",
                session_id="redaction",
                context={
                    "known": ["provider configured"],
                    "api_key": "never-store-this-secret",
                    "nested": {"authorization": "Bearer never-store-this"},
                },
            )
            raw_ledger = (Path(tmp) / "intelligence" / "activity_ledger.jsonl").read_text(encoding="utf-8")
            raw_memory = (Path(tmp) / "intelligence" / "working_memory.json").read_text(encoding="utf-8")
            self.assertNotIn("never-store-this-secret", raw_ledger)
            self.assertNotIn("Bearer never-store-this", raw_ledger)
            self.assertNotIn("never-store-this-secret", raw_memory)
            self.assertIn("[REDACTED]", raw_ledger)

    def test_verification_requires_named_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = self.make_brain(tmp)
            brain.plan("test API", session_id="verify")
            blocked = brain.verify(
                session_id="verify",
                evidence={"tests": "passed"},
                required_evidence=("tests", "commit_sha"),
            )
            self.assertFalse(blocked.verified)
            self.assertEqual(("commit_sha",), blocked.missing_evidence)

            verified = brain.verify(
                session_id="verify",
                evidence={"tests": "passed", "commit_sha": "abc123"},
                required_evidence=("tests", "commit_sha"),
            )
            self.assertTrue(verified.verified)
            self.assertEqual("verified", verified.conclusion)

    def test_ledger_file_is_valid_json_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = self.make_brain(tmp)
            brain.plan("research system state", session_id="jsonl")
            path = Path(tmp) / "intelligence" / "activity_ledger.jsonl"
            events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual("brain.plan.created", events[-1]["event_type"])
            self.assertEqual("jsonl", events[-1]["session_id"])


if __name__ == "__main__":
    unittest.main()
