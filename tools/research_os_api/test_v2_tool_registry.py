#!/usr/bin/env python3
from __future__ import annotations

import unittest

from v2_tool_registry import (
    TOOL_MATCHING_CONTRACT,
    TOOL_REGISTRY_CONTRACT,
    ToolDefinition,
    ToolRegistry,
)


class ToolRegistryTests(unittest.TestCase):
    def test_core_tools_are_metadata_only_until_adapter_is_attached(self) -> None:
        registry = ToolRegistry()
        report = registry.dashboard()
        self.assertEqual("brain-tools-phase-3", TOOL_REGISTRY_CONTRACT)
        self.assertEqual(TOOL_REGISTRY_CONTRACT, report["contract"])
        self.assertEqual(TOOL_MATCHING_CONTRACT, report["matching_contract"])
        self.assertEqual(3, report["tool_count"])
        self.assertEqual(3, report["enabled_count"])
        self.assertEqual(0, report["ready_count"])
        self.assertEqual(0, report["mutating_count"])
        self.assertEqual("permissioned_execution_controller_only", report["execution_boundary"])

    def test_adapter_registration_makes_tool_ready(self) -> None:
        registry = ToolRegistry()
        registry.register_adapter(
            "brain.skills.inspect",
            lambda action, payload, dry_run: {"action": action, "dry_run": dry_run},
        )
        item = registry.describe("brain.skills.inspect")
        self.assertTrue(item["adapter_ready"])
        self.assertTrue(item["ready"])
        result = registry.invoke("brain.skills.inspect", "list", {}, dry_run=False)
        self.assertEqual("list", result["action"])

    def test_disabled_tool_cannot_receive_executable_adapter(self) -> None:
        registry = ToolRegistry(())
        registry.register(
            ToolDefinition(
                "test.disabled",
                "1.0.0",
                "Disabled",
                "Disabled tool contract.",
                ("disabled_test",),
                enabled=False,
            )
        )
        with self.assertRaisesRegex(ValueError, "tool disabled"):
            registry.register_adapter(
                "test.disabled",
                lambda action, payload, dry_run: {"ok": True},
            )
        self.assertFalse(registry.describe("test.disabled")["ready"])

    def test_mutating_tool_contract_requires_explicit_metadata(self) -> None:
        registry = ToolRegistry(())
        registry.register(
            ToolDefinition(
                "test.write-state",
                "1.0.0",
                "Write State",
                "Test-only state mutation contract.",
                ("state_write",),
                permissions=("state.write",),
                mutating=True,
                idempotent=True,
            )
        )
        item = registry.describe("test.write-state")
        self.assertTrue(item["mutating"])
        self.assertFalse(item["ready"])

    def test_destructive_tool_cannot_be_declared_read_only(self) -> None:
        registry = ToolRegistry(())
        with self.assertRaises(ValueError):
            registry.register(
                ToolDefinition(
                    "test.invalid-delete",
                    "1.0.0",
                    "Invalid Delete",
                    "Invalid destructive declaration.",
                    ("delete",),
                    destructive=True,
                    mutating=False,
                )
            )

    def test_discovery_can_require_ready_adapter(self) -> None:
        registry = ToolRegistry()
        self.assertEqual([], registry.discover(capability="skill_registry", ready_only=True))
        registry.register_adapter(
            "brain.skills.inspect",
            lambda action, payload, dry_run: {"ok": True},
        )
        matches = registry.discover(capability="skill_registry", ready_only=True)
        self.assertEqual(["brain.skills.inspect"], [item["tool_id"] for item in matches])

    def test_capability_match_requires_one_ready_tool_to_satisfy_all_capabilities(self) -> None:
        registry = ToolRegistry(())
        registry.register(
            ToolDefinition(
                "test.multi",
                "1.0.0",
                "Multi",
                "Satisfies two capabilities.",
                ("cap_a", "cap_b"),
            )
        )
        registry.register(
            ToolDefinition(
                "test.partial",
                "1.0.0",
                "Partial",
                "Satisfies only one capability.",
                ("cap_a",),
            )
        )
        registry.register_adapter("test.multi", lambda action, payload, dry_run: {"ok": True})
        registry.register_adapter("test.partial", lambda action, payload, dry_run: {"ok": True})
        match = registry.match_capabilities(("cap_a", "cap_b"), ready_only=True)
        self.assertEqual(TOOL_MATCHING_CONTRACT, match["contract"])
        self.assertTrue(match["matched"])
        self.assertEqual(["test.multi"], match["candidates"])
        self.assertEqual("test.multi", match["selected_tool_id"])

    def test_capability_match_reports_missing_without_guessing(self) -> None:
        registry = ToolRegistry(())
        match = registry.match_capabilities(("unknown_capability",), ready_only=True)
        self.assertFalse(match["matched"])
        self.assertIsNone(match["selected_tool_id"])
        self.assertEqual(("unknown_capability",), match["missing_capabilities"])


if __name__ == "__main__":
    unittest.main()
