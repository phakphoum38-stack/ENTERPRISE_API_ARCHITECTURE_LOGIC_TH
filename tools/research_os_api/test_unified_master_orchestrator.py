#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from unified_master_orchestrator import UNIFIED_VERSION, UnifiedMasterOrchestrator


class UnifiedMasterOrchestratorTests(unittest.TestCase):
    def test_manifest_combines_independent_owners_without_shared_authority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            master = UnifiedMasterOrchestrator(Path(tmp))
            manifest = master.manifest()

        self.assertEqual(manifest["version"], UNIFIED_VERSION)
        self.assertTrue(manifest["single_master_owner"])
        self.assertEqual(manifest["factory_profiles"], ["1^3", "3^3", "6^3", "6^6"])
        self.assertEqual(manifest["capacity"]["assistant_6x3_capacity"], 216)
        self.assertEqual(manifest["capacity"]["max_leaf_capacity"], 46656)
        self.assertEqual(
            manifest["owners"]["cyber_web_security"],
            "v2_cyber_web_standard.CyberWebSecurityStandard",
        )
        self.assertEqual(
            manifest["owners"]["file_ownership"],
            "v2_file_ownership_boundary.FileOwnershipBoundary",
        )
        separation = manifest["owner_boundaries"]
        self.assertFalse(separation["shared_authority"])
        self.assertFalse(separation["security_may_change_file_owner"])
        self.assertFalse(separation["security_may_grant_file_acl"])
        self.assertFalse(separation["file_owner_may_override_security_policy"])
        self.assertFalse(separation["file_owner_may_disable_security_controls"])
        self.assertFalse(separation["standalone_owner_package_contains_security_owner"])
        self.assertFalse(manifest["invariants"]["all_workers_started_by_default"])
        self.assertFalse(manifest["invariants"]["duplicate_dependency_graph"])
        self.assertFalse(manifest["invariants"]["standalone_owner_package_contains_security_owner"])
        self.assertEqual(
            manifest["invariants"]["canonical_dependency_graph"],
            "AgentOrchestrator",
        )

    def test_plan_keeps_owner_and_security_results_separate(self) -> None:
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
        self.assertEqual(result["cyber_web_security"]["owner"], "CyberWebSecurityStandard")
        self.assertFalse(result["cyber_web_security"]["changes_file_ownership"])
        self.assertFalse(result["cyber_web_security"]["grants_file_acl"])
        self.assertEqual(result["file_ownership"]["owner"], "FileOwnershipBoundary")
        self.assertFalse(result["file_ownership"]["ownership_change_performed"])
        self.assertFalse(result["file_ownership"]["acl_change_performed"])
        self.assertFalse(result["owner_separation"]["shared_authority"])
        self.assertFalse(
            result["owner_separation"]["standalone_owner_package_contains_security_owner"]
        )
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
        self.assertNotIn("cross_owner_contract", file_ownership)

    def test_cyber_assessment_never_changes_file_owner_or_grants_acl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            master = UnifiedMasterOrchestrator(Path(tmp))
            manifest = master.cyber_web_security.manifest()
            evidence = {
                item["evidence_key"]: True
                for item in manifest["controls"]
                if item["required_public"]
            }
            result = master.assess_cyber_web_security(evidence)

        self.assertTrue(result["ready"])
        self.assertFalse(result["changes_file_ownership"])
        self.assertFalse(result["grants_permissions"])


if __name__ == "__main__":
    unittest.main()
