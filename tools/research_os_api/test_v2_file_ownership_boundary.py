#!/usr/bin/env python3
from __future__ import annotations

import unittest

from v2_file_ownership_boundary import (
    FILE_OWNERSHIP,
    FILE_OWNERSHIP_CONTRACT,
)


class FileOwnershipBoundaryTests(unittest.TestCase):
    def test_manifest_declares_standalone_file_ownership_boundary(self) -> None:
        manifest = FILE_OWNERSHIP.manifest()
        self.assertEqual(manifest["contract"], FILE_OWNERSHIP_CONTRACT)
        self.assertEqual(manifest["owner"], "FileOwnershipBoundary")
        self.assertEqual(manifest["implementation_state"], "boundary_only")
        self.assertFalse(manifest["operating_system_acl_backend"])
        self.assertFalse(manifest["changes_file_owner"])
        self.assertFalse(manifest["grants_file_acl"])
        self.assertFalse(manifest["reads_private_file_metadata"])
        self.assertEqual(
            manifest["authorization_source"],
            "dedicated_file_ownership_backend_required",
        )

    def test_plan_is_read_only_until_dedicated_backend_exists(self) -> None:
        plan = FILE_OWNERSHIP.plan()
        self.assertEqual(plan["mode"], "boundary_only")
        self.assertFalse(plan["ownership_change_performed"])
        self.assertFalse(plan["acl_change_performed"])
        self.assertTrue(plan["requires_dedicated_backend_for_mutation"])
        self.assertTrue(plan["requires_explicit_authorization_for_mutation"])


if __name__ == "__main__":
    unittest.main()
