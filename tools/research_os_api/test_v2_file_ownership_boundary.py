#!/usr/bin/env python3
from __future__ import annotations

import unittest

from v2_file_ownership_boundary import (
    FILE_OWNERSHIP,
    FILE_OWNERSHIP_CONTRACT,
)


class FileOwnershipBoundaryTests(unittest.TestCase):
    def test_manifest_contains_only_three_owner_scopes(self) -> None:
        manifest = FILE_OWNERSHIP.manifest()
        self.assertEqual(manifest["contract"], FILE_OWNERSHIP_CONTRACT)
        self.assertEqual(manifest["owner"], "FileOwnershipBoundary")
        self.assertEqual(
            manifest["scope"],
            ["file_ownership", "filesystem_acl", "document_ownership"],
        )
        self.assertEqual(manifest["implementation_state"], "boundary_only")
        self.assertFalse(manifest["changes_file_owner"])
        self.assertFalse(manifest["grants_file_acl"])
        self.assertFalse(manifest["changes_document_owner"])

    def test_plan_is_read_only_for_the_same_three_scopes(self) -> None:
        plan = FILE_OWNERSHIP.plan()
        self.assertEqual(
            plan["scope"],
            ["file_ownership", "filesystem_acl", "document_ownership"],
        )
        self.assertEqual(plan["mode"], "boundary_only")
        self.assertFalse(plan["ownership_change_performed"])
        self.assertFalse(plan["acl_change_performed"])
        self.assertFalse(plan["document_ownership_change_performed"])


if __name__ == "__main__":
    unittest.main()
