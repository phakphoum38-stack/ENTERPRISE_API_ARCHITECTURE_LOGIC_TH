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
        self.assertEqual(
            manifest["owners"]["cyber_web_security"],
            "v2_cyber_web_standard.CyberWebSecurityStandard",
        )
        self.assertEqual(
            manifest["owners"]["file_ownership"],
            "v2_file_ownership_boundary.FileOwnershipBoundary",
        )

        cyber_boundary = manifest["owner_boundaries"]["cyber_web_security"]
        file_boundary = manifest["owner_boundaries"]["file_ownership"]
        self.assertTrue(cyber_boundary["separate_from_file_owner_system"])
        self.assertFalse(cyber_boundary["file_owner_write_authority"])
        self.assertFalse(cyber_boundary["file_acl_grant_authority"])
        self.assertTrue(file_boundary["separate_from_cyber_web_security"])
        self.assertFalse(file_boundary["cyber_may_change_file_owner"])
        self.assertFalse(file_boundary["cyber_may_grant_file_acl"])
        self.assertFalse(file_boundary["shared_authority"])
        self.assertFalse(manifest["owner_boundaries"]["shared_authority"])

        self.assertFalse(manifest["invariants"]["all_workers_started_by_default"])
        self.assertFalse(manifest["invariants"]["duplicate_dependency_graph"])
        self.assertFalse(manifest["invariants"]["external_tools_auto_downloaded"])
        self.assertFalse(manifest["invariants"]["external_tools_auto_installed"])
        self.assertFalse(manifest["invariants"]["external_tools_auto_executed"])
        self.assertTrue(manifest["invariants"]["cyber_security_separate_from_file_ownership"])
        self.assertFalse(manifest["invariants"]["cyber_security_can_change_file_owner"])
        self.assertFalse(manifest["invariants"]["cyber_security_can_grant_file_acl"])
        self.assertFalse(manifest["invariants"]["file_ownership_can_override_cyber_policy"])
        self.assertFalse(manifest["invariants"]["file_ownership_can_disable_security_controls"])
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

        self.assertTrue(result["cyber_web_security"]["separate_from_file_owner_system"])
        self.assertFalse(result["cyber_web_security"]["changes_file_ownership"])
        self.assertFalse(result["cyber_web_security"]["grants_file_acl"])
        self.assertEqual(result["file_ownership"]["owner"], "FileOwnershipBoundary")
        self.assertFalse(result["file_ownership"]["ownership_change_performed"])
        self.assertFalse(result["file_ownership"]["acl_change_performed"])
        self.assertFalse(result["file_ownership"]["cyber_security_involved"])

        self.assertFalse(result["execution"]["performed"])
        self.assertFalse(result["execution"]["approval_bypassed"])
        self.assertFalse(result["execution"]["external_tool_installed"])
        self.assertFalse(result["execution"]["external_tool_executed"])
        self.assertFalse(result["execution"]["file_owner_changed"])
        self.assertFalse(result["execution"]["file_acl_granted"])

    def test_status_exposes_tool_cyber_and_file_ownership_as_separate_owners(self) -> None:
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

        cyber = status["cyber_web_security"]
        self.assertEqual(cyber["owner"], "CyberWebSecurityStandard")
        self.assertEqual(cyber["target"]["owasp_asvs"], "5.0.0 Level 2 baseline")
        self.assertTrue(cyber["boundary"]["separate_from_file_owner_system"])
        self.assertFalse(cyber["boundary"]["file_owner_write_authority"])
        self.assertFalse(cyber["permission_grant_authority"])

        file_ownership = status["file_ownership"]
        self.assertEqual(file_ownership["owner"], "FileOwnershipBoundary")
        self.assertEqual(file_ownership["implementation_state"], "boundary_only")
        self.assertFalse(file_ownership["cyber_security_authority"])
        self.assertFalse(file_ownership["web_security_policy_authority"])
        self.assertFalse(file_ownership["changes_file_owner"])
        self.assertFalse(file_ownership["grants_file_acl"])

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
        self.assertTrue(result["boundary"]["separate_from_file_owner_system"])

    def test_file_ownership_status_is_boundary_only_and_does_not_change_cyber_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            master = UnifiedMasterOrchestrator(Path(tmp))
            status = master.file_ownership_status()

        self.assertEqual(status["owner"], "FileOwnershipBoundary")
        self.assertEqual(status["implementation_state"], "boundary_only")
        self.assertFalse(status["web_security_policy_authority"])
        self.assertFalse(status["cross_owner_contract"]["file_owner_may_override_cyber_policy"])
        self.assertFalse(status["cross_owner_contract"]["file_owner_may_disable_security_controls"])


if __name__ == "__main__":
    unittest.main()
