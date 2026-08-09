#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest

from agent_platform import AgentRegistry
from v2_brain_core import ActivityLedger, WorkingMemory
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


if __name__ == "__main__":
    unittest.main()
