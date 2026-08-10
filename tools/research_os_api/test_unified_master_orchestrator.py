#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from unified_master_orchestrator import UNIFIED_VERSION, UnifiedMasterOrchestrator


class UnifiedMasterOrchestratorTests(unittest.TestCase):
    def test_manifest_combines_all_existing_owners_without_eager_spawn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            master = UnifiedMasterOrchestrator(Path(tmp))
            manifest = master.manifest()

        self.assertEqual(manifest["version"], UNIFIED_VERSION)
        self.assertTrue(manifest["single_master_owner"])
        self.assertEqual(manifest["factory_profiles"], ["1^3", "3^3", "6^3", "6^6"])
        self.assertEqual(manifest["capacity"]["assistant_6x3_capacity"], 216)
        self.assertEqual(manifest["capacity"]["max_leaf_capacity"], 46656)
        self.assertEqual(
            manifest["owners"]["tool_intelligence"],
            "v2_tool_intelligence.ToolIntelligence",
        )
        self.assertFalse(manifest["invariants"]["all_workers_started_by_default"])
        self.assertFalse(manifest["invariants"]["duplicate_dependency_graph"])
        self.assertFalse(manifest["invariants"]["external_tools_auto_downloaded"])
        self.assertFalse(manifest["invariants"]["external_tools_auto_installed"])
        self.assertFalse(manifest["invariants"]["external_tools_auto_executed"])
        self.assertEqual(
            manifest["invariants"]["canonical_dependency_graph"],
            "AgentOrchestrator",
        )

    def test_plan_combines_compound_governed_tool_and_factory_planning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            master = UnifiedMasterOrchestrator(Path(tmp))
            result = master.plan(
                "วางแผนผู้ช่วย 6^3 สำหรับ Research OS และระบบ API",
                context={"required_tool_capabilities": ["api_integration"]},
                versions=(UNIFIED_VERSION,),
            )

        self.assertEqual(result["contract"], "unified-master-orchestrator-v3")
        self.assertEqual(result["factory"]["profile"], "1^3")
        self.assertEqual(result["factory"]["active_factories"], 1)
        self.assertEqual(
            result["compound_brain"]["assistant_profile"]["mode"],
            "assistant_6x3",
        )
        self.assertLessEqual(
            result["compound_brain"]["hierarchy"]["active_workers"],
            result["compound_brain"]["hierarchy"]["max_active_workers"],
        )
        self.assertEqual(
            result["tool_intelligence"]["contract"],
            "brain-tool-intelligence-v1",
        )
        self.assertIn(
            "api_integration",
            result["tool_intelligence"]["required_capabilities"],
        )
        self.assertFalse(result["tool_intelligence"]["execution_performed"])
        self.assertFalse(result["execution"]["performed"])
        self.assertFalse(result["execution"]["approval_bypassed"])
        self.assertFalse(result["execution"]["external_tool_installed"])
        self.assertFalse(result["execution"]["external_tool_executed"])

    def test_status_exposes_tool_training_policy_without_secret_or_execution_authority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            master = UnifiedMasterOrchestrator(Path(tmp))
            status = master.status()

        tool_intelligence = status["tool_intelligence"]
        self.assertEqual(tool_intelligence["contract"], "brain-tool-intelligence-v1")
        self.assertFalse(tool_intelligence["policy"]["automatic_download"])
        self.assertFalse(tool_intelligence["policy"]["automatic_install"])
        self.assertFalse(tool_intelligence["policy"]["automatic_execution"])
        self.assertTrue(tool_intelligence["policy"]["review_required"])
        self.assertFalse(tool_intelligence["external_tool_execution"])


if __name__ == "__main__":
    unittest.main()
