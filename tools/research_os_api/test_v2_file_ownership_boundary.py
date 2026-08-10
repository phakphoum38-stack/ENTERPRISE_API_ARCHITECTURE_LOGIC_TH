#!/usr/bin/env python3
from __future__ import annotations

import unittest

from v2_file_ownership_boundary import (
    FILE_OWNERSHIP,
    FILE_OWNERSHIP_CONTRACT,
)


class FileOwnershipBoundaryTests(unittest.TestCase):
    def test_manifest_declares_independent_owner_and_no_cyber_authority(self) -> None:
        manifest = FILE_OWNERSHIP.manifest()
        self.assertEqual(manifest["contract"], FILE_OWNERSHIP_CONTRACT)
        self.assertEqual(manifest["owner"], "FileOwnershipBoundary")
        self.assertEqual(manifest["implementation_state"], "boundary_only")
        self.assertFalse(manifest["operating_system_acl_backend"])
        self.assertFalse(manifest["changes_file_owner"])
        self.assertFalse(manifest["grants_file_acl"])
        self.assertFalse(manifest["cyber_security_authority"])
        self.assertFalse(manifest["web_security_policy_authority"])

    def test_cross_owner_contract_has_no_shared_authority(self) -> None:
        boundary = FILE_OWNERSHIP.cyber_boundary()
        self.assertTrue(boundary["separate_from_cyber_web_security"])
        self.assertEqual(boundary["cyber_web_owner"], "CyberWebSecurityStandard")
        self.assertEqual(boundary["file_ownership_owner"], "FileOwnershipBoundary")
        self.assertFalse(boundary["cyber_may_change_file_owner"])
        self.assertFalse(boundary["cyber_may_grant_file_acl"])
        self.assertFalse(boundary["file_owner_may_override_cyber_policy"])
        self.assertFalse(boundary["file_owner_may_disable_security_controls"])
        self.assertFalse(boundary["shared_authority"])

    def test_plan_is_read_only_until_dedicated_backend_exists(self) -> None:
        plan = FILE_OWNERSHIP.plan()
        self.assertEqual(plan["mode"], "boundary_only")
        self.assertFalse(plan["ownership_change_performed"])
        self.assertFalse(plan["acl_change_performed"])
        self.assertTrue(plan["requires_dedicated_backend_for_mutation"])
        self.assertTrue(plan["requires_explicit_authorization_for_mutation"])
        self.assertFalse(plan["cyber_security_involved"])


if __name__ == "__main__":
    unittest.main()
