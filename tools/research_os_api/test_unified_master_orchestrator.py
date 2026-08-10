#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from unified_master_orchestrator import UNIFIED_VERSION, UnifiedMasterOrchestrator


class UnifiedMasterOrchestratorTests(unittest.TestCase):
    def test_manifest_combines_existing_owners_without_eager_spawn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            master = UnifiedMasterOrchestrator(Path(tmp))
            manifest = master.manifest()

        self.assertEqual(manifest["version"], UNIFIED_VERSION)
        self.assertTrue(manifest["single_master_owner"])
        self.assertEqual(manifest["factory_profiles"], ["1^3", "3^3", "6^3", "6^6"])
        self.assertEqual(manifest["capacity"]["assistant_6x3_capacity"], 216)
        self.assertEqual(manifest["capacity"]["max_leaf_capacity"], 46656)
        self.assertEqual(
            manifest["owners"]["file_ownership"],
            "v2_file_ownership_boundary.FileOwnershipBoundary",
        )
        self.assertFalse(manifest["invariants"]["all_workers_started_by_default"])
        self.assertFalse(manifest["invariants"]["duplicate_dependency_graph"])
        self.assertEqual(
            manifest["invariants"]["canonical_dependency_graph"],
            "AgentOrchestrator",
        )

    def test_plan_combines_brain_tools_owner_and_factory_planning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            master = UnifiedMasterOrchestrator(Path(tmp))
            result = master.plan(
                "วางแผนผู้ช่วย 6^3 สำหรับ Research OS และระบบ API",
                context={"required_tool_capabilities": ["api_integration"]},
                versions=(UNIFIED_VERSION,),
            )

        self.assertEqual(result["contract"], "unified-master-orchestrator-v3")
        self.assertEqual(result["factory"]["profile"], "1^3")
        self.assertEqual(
            result["compound_brain"]["assistant_profile"]["mode"],
            "assistant_6x3",
        )
        self.assertFalse(result["tool_intelligence"]["execution_performed"])
        self.assertEqual(result["file_ownership"]["owner"], "FileOwnershipBoundary")
        self.assertFalse(result["file_ownership"]["ownership_change_performed"])
        self.assertFalse(result["file_ownership"]["acl_change_performed"])
        self.assertFalse(result["execution"]["performed"])
        self.assertFalse(result["execution"]["file_owner_changed"])
        self.assertFalse(result["execution"]["file_acl_granted"])

    def test_status_exposes_file_owner_as_standalone_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            master = UnifiedMasterOrchestrator(Path(tmp))
            status = master.status()

        file_ownership = status["file_ownership"]
        self.assertEqual(file_ownership["contract"], "research-os-file-ownership-boundary-v2")
        self.assertEqual(file_ownership["owner"], "FileOwnershipBoundary")
        self.assertEqual(file_ownership["implementation_state"], "boundary_only")
        self.assertFalse(file_ownership["changes_file_owner"])
        self.assertFalse(file_ownership["grants_file_acl"])


if __name__ == "__main__":
    unittest.main()
