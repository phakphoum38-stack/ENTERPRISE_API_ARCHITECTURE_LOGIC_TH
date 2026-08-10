#!/usr/bin/env python3
from __future__ import annotations

import unittest

from v2_domain_skills import DOMAIN_SKILLS, PACKS, catalog, install_domain_skill_packs
from v2_skill_registry import SkillRegistry


class DomainSkillPackTests(unittest.TestCase):
    def test_all_packs_install_without_granting_tools_or_permissions(self) -> None:
        registry = SkillRegistry()
        report = install_domain_skill_packs(registry)
        self.assertEqual(len(DOMAIN_SKILLS), report["total_domain_skills"])
        self.assertFalse(report["permission_grants"])
        self.assertFalse(report["tool_adapters_created"])
        self.assertFalse(report["provider_specific"])
        self.assertGreaterEqual(registry.dashboard()["skill_count"], len(DOMAIN_SKILLS) + 3)

    def test_dependency_graph_resolves_representative_domain_skills(self) -> None:
        registry = SkillRegistry()
        install_domain_skill_packs(registry)
        order = registry.resolve_dependencies((
            "github.ci-diagnosis",
            "shift.calendar-change-plan",
            "reliability.recovery-plan",
        ))
        self.assertLess(order.index("software.code-search"), order.index("software.debug-diagnosis"))
        self.assertLess(order.index("github.repository-status"), order.index("github.ci-diagnosis"))
        self.assertLess(order.index("shift.roster-reading"), order.index("shift.conflict-analysis"))
        self.assertLess(order.index("shift.conflict-analysis"), order.index("shift.replacement-planning"))
        self.assertLess(order.index("reliability.incident-diagnosis"), order.index("reliability.recovery-plan"))

    def test_domain_catalog_covers_project_skill_families(self) -> None:
        report = catalog()
        self.assertEqual(set(PACKS), set(report["packs"]))
        self.assertGreaterEqual(report["skill_count"], 30)
        self.assertIn("software_development", report["packs"])
        self.assertIn("github_ci", report["packs"])
        self.assertIn("documents_data", report["packs"])
        self.assertIn("google_workspace", report["packs"])
        self.assertIn("shift_scheduling", report["packs"])
        self.assertTrue(report["invariants"]["missing_adapter_fails_closed"])

    def test_skill_registration_does_not_claim_tool_execution(self) -> None:
        registry = SkillRegistry()
        install_domain_skill_packs(registry, packs=("software_development",))
        item = registry.describe("software.controlled-build")
        self.assertTrue(item["ready"])
        self.assertEqual(("build_execution",), tuple(item["required_tool_capabilities"]))
        # Skill readiness is dependency readiness. Runtime Tool Introspection is
        # the separate source of truth for whether a real adapter is executable.
        self.assertNotIn("adapter_ready", item)

    def test_unknown_pack_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown domain skill pack"):
            install_domain_skill_packs(SkillRegistry(), packs=("not-real",))


if __name__ == "__main__":
    unittest.main()
