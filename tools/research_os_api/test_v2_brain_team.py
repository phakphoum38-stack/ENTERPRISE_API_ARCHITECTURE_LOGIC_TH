#!/usr/bin/env python3
from __future__ import annotations

import unittest

from agent_platform import AgentRegistry
from v2_brain_team import BRAIN_TEAM, BRAIN_TEAM_IDS, brain_team_dashboard, register_brain_team


class BrainTeamTests(unittest.TestCase):
    def test_team_has_at_least_ten_unique_agents(self) -> None:
        self.assertGreaterEqual(len(BRAIN_TEAM), 10)
        self.assertEqual(12, len(BRAIN_TEAM))
        self.assertEqual(len(BRAIN_TEAM_IDS), len(set(BRAIN_TEAM_IDS)))

    def test_team_is_isolated_and_registers_without_replacing_core_agents(self) -> None:
        registry = AgentRegistry()
        core_before = {item["agent_id"] for item in registry.list()}
        register_brain_team(registry)
        all_after = {item["agent_id"] for item in registry.list()}
        self.assertTrue(core_before <= all_after)
        self.assertTrue(set(BRAIN_TEAM_IDS) <= all_after)
        self.assertFalse(core_before & set(BRAIN_TEAM_IDS))

    def test_registration_is_idempotent(self) -> None:
        registry = AgentRegistry()
        register_brain_team(registry)
        count = len(registry.list())
        register_brain_team(registry)
        self.assertEqual(count, len(registry.list()))

    def test_every_writer_requires_confirmation_and_reviewer_is_read_only(self) -> None:
        for agent in BRAIN_TEAM:
            if agent.agent_id == "v2_brain_reviewer":
                self.assertEqual("read_only", agent.permission_profile)
                self.assertFalse(any("write" in permission for permission in agent.permissions))
                continue
            if any("write" in permission for permission in agent.permissions):
                self.assertEqual("write_confirmed", agent.permission_profile)
                self.assertTrue(any(permission.endswith("with_confirmation") for permission in agent.permissions))

    def test_dashboard_reports_minimum_team_requirement_satisfied(self) -> None:
        registry = AgentRegistry()
        register_brain_team(registry)
        dashboard = brain_team_dashboard(registry)
        self.assertEqual(12, dashboard["member_count"])
        self.assertEqual(12, dashboard["ready_count"])
        self.assertEqual(10, dashboard["minimum_required"])
        self.assertTrue(dashboard["minimum_satisfied"])

    def test_reviewer_has_no_fallback_to_implementation_agents(self) -> None:
        reviewer = next(item for item in BRAIN_TEAM if item.agent_id == "v2_brain_reviewer")
        self.assertEqual((), reviewer.fallback_agents)
        self.assertIn("independent_review", reviewer.capabilities)


if __name__ == "__main__":
    unittest.main()
