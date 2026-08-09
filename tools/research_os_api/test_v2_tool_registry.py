#!/usr/bin/env python3
from __future__ import annotations

import unittest

from v2_tool_registry import TOOL_REGISTRY_CONTRACT, ToolDefinition, ToolRegistry


class ToolRegistryTests(unittest.TestCase):
    def test_core_tools_are_metadata_only_until_adapter_is_attached(self) -> None:
        registry = ToolRegistry()
        report = registry.dashboard()
        self.assertEqual("brain-tools-phase-3", TOOL_REGISTRY_CONTRACT)
        self.assertEqual(TOOL_REGISTRY_CONTRACT, report["contract"])
        self.assertEqual(3, report["tool_count"])
        self.assertEqual(0, report["ready_count"])
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


if __name__ == "__main__":
    unittest.main()
