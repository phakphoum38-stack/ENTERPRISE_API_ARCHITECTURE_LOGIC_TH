#!/usr/bin/env python3
from __future__ import annotations

import unittest

from agent_platform import AgentRegistry
from v2_capability_graph import CapabilityGraph
from v2_domain_skills import install_domain_skill_packs
from v2_skill_registry import SkillRegistry
from v2_tool_registry import ToolDefinition, ToolRegistry


class CapabilityGraphTests(unittest.TestCase):
    def test_graph_is_projection_not_duplicate_registry(self) -> None:
        skills = SkillRegistry()
        install_domain_skill_packs(skills)
        tools = ToolRegistry()
        graph = CapabilityGraph(agents=AgentRegistry(), skills=skills, tools=tools)
        snapshot = graph.snapshot()
        self.assertFalse(snapshot["persisted"])
        self.assertFalse(snapshot["duplicate_registry"])
        self.assertGreater(snapshot["counts"]["nodes"], 0)
        self.assertGreater(snapshot["counts"]["edges"], 0)

    def test_resolve_distinguishes_routable_skill_and_executable(self) -> None:
        skills = SkillRegistry()
        install_domain_skill_packs(skills)
        tools = ToolRegistry(
            (
                ToolDefinition(
                    "test.code.search",
                    "1.0.0",
                    "Code Search",
                    "Test adapter contract.",
                    ("code_search",),
                    permissions=("workspace.read",),
                ),
            )
        )
        tools.register_adapter(
            "test.code.search",
            lambda action, payload, dry_run: {"matches": []},
        )
        graph = CapabilityGraph(agents=AgentRegistry(), skills=skills, tools=tools)
        result = graph.resolve(("debug",))
        item = result["capabilities"][0]
        self.assertTrue(item["known"])
        self.assertTrue(item["routable"])
        self.assertTrue(item["skill_supported"])
        route = next(
            value
            for value in item["skill_routes"]
            if value["skill_id"] == "software.code-search"
        )
        self.assertTrue(route["executable"])
        self.assertEqual(["test.code.search"], route["tool_candidates"])

    def test_unknown_capability_remains_unknown(self) -> None:
        graph = CapabilityGraph(
            agents=AgentRegistry(),
            skills=SkillRegistry(),
            tools=ToolRegistry(),
        )
        result = graph.resolve(("capability_that_does_not_exist",))
        item = result["capabilities"][0]
        self.assertFalse(item["known"])
        self.assertFalse(item["routable"])
        self.assertFalse(item["skill_supported"])
        self.assertFalse(result["all_known"])


if __name__ == "__main__":
    unittest.main()
