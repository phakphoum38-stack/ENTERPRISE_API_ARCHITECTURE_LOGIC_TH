#!/usr/bin/env python3
from __future__ import annotations

import unittest

from v2_skill_registry import (
    CORE_BRAIN_SKILLS,
    SKILL_REGISTRY_CONTRACT,
    SkillDefinition,
    SkillRegistry,
)


class SkillRegistryTests(unittest.TestCase):
    def test_core_brain_skills_are_ready(self) -> None:
        registry = SkillRegistry()
        dashboard = registry.dashboard()
        self.assertEqual(SKILL_REGISTRY_CONTRACT, dashboard["contract"])
        self.assertEqual("skill_to_tool_executor", dashboard["execution"])
        self.assertEqual(len(CORE_BRAIN_SKILLS), dashboard["skill_count"])
        self.assertEqual(len(CORE_BRAIN_SKILLS), dashboard["ready_count"])
        self.assertIn("verification", dashboard["capabilities"])
        self.assertIn("context_engine", registry.get("brain.goal-analysis").required_tool_capabilities)
        self.assertIn("session_inspection", registry.get("brain.evidence-verification").required_tool_capabilities)

    def test_dynamic_skill_discovery_uses_capabilities(self) -> None:
        registry = SkillRegistry(())
        registry.register(
            SkillDefinition(
                "developer.github-ci-debug",
                "1.0.0",
                "GitHub CI Debug",
                "Debugs CI from exact workflow evidence.",
                ("github_ci_debug", "root_cause"),
                required_tools=("github.read",),
                required_tool_capabilities=("github_workflow_read",),
                permissions=("github.read",),
                required_evidence=("head_sha", "failed_step"),
            )
        )
        matches = registry.discover(capability="github_ci_debug")
        self.assertEqual(["developer.github-ci-debug"], [item["skill_id"] for item in matches])
        self.assertEqual(
            ("github_workflow_read",),
            registry.get("developer.github-ci-debug").required_tool_capabilities,
        )

    def test_dependencies_are_resolved_dependency_first(self) -> None:
        registry = SkillRegistry(())
        registry.register(
            SkillDefinition("skill.base", "1.0.0", "Base", "Base skill.", ("base",))
        )
        registry.register(
            SkillDefinition(
                "skill.child",
                "1.0.0",
                "Child",
                "Child skill.",
                ("child",),
                required_skills=("skill.base",),
            )
        )
        self.assertEqual(("skill.base", "skill.child"), registry.resolve_dependencies(("skill.child",)))

    def test_dependency_cycle_is_rejected_at_resolution(self) -> None:
        registry = SkillRegistry(())
        registry.register(
            SkillDefinition("skill.alpha", "1.0.0", "Alpha", "Alpha skill.", ("alpha",), required_skills=("skill.beta",))
        )
        registry.register(
            SkillDefinition("skill.beta", "1.0.0", "Beta", "Beta skill.", ("beta",), required_skills=("skill.alpha",))
        )
        with self.assertRaisesRegex(ValueError, "cycle"):
            registry.resolve_dependencies(("skill.alpha",))

    def test_missing_dependency_makes_skill_not_ready(self) -> None:
        registry = SkillRegistry(())
        registry.register(
            SkillDefinition(
                "skill.waiting",
                "1.0.0",
                "Waiting",
                "Waiting for dependency.",
                ("waiting",),
                required_skills=("skill.missing",),
            )
        )
        state = registry.describe("skill.waiting")
        self.assertFalse(state["ready"])
        self.assertEqual(["skill.missing"], state["missing_dependencies"])

    def test_duplicate_tool_capability_requirement_is_rejected(self) -> None:
        registry = SkillRegistry(())
        with self.assertRaisesRegex(ValueError, "duplicate required tool capability"):
            registry.register(
                SkillDefinition(
                    "skill.duplicate-tool-cap",
                    "1.0.0",
                    "Duplicate Tool Capability",
                    "Invalid duplicate capability declaration.",
                    ("duplicate",),
                    required_tool_capabilities=("read", "read"),
                )
            )

    def test_invalid_contract_is_rejected(self) -> None:
        registry = SkillRegistry(())
        with self.assertRaises(ValueError):
            registry.register(SkillDefinition("BAD", "1", "Bad", "Bad skill.", ("bad",)))


if __name__ == "__main__":
    unittest.main()
