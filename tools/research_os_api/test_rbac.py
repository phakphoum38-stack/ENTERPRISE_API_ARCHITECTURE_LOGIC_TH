from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rbac import AuthorizationError, Principal, Role, RoleStore


class RbacTests(unittest.TestCase):
    def test_default_user_and_environment_roles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(
                os.environ,
                {
                    "RESEARCH_OS_OWNER_EMAILS": "owner@example.com",
                    "RESEARCH_OS_PRO_EMAILS": "pro@example.com",
                },
                clear=False,
            ):
                store = RoleStore(Path(tmp) / "roles.json")
                self.assertEqual(store.resolve("user@example.com").role, Role.USER)
                self.assertEqual(store.resolve("pro@example.com").role, Role.PRO)
                self.assertEqual(store.resolve("owner@example.com").role, Role.OWNER)

    def test_only_owner_can_assign_and_persist_roles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "roles.json"
            store = RoleStore(path)
            owner = Principal("owner@example.com", Role.OWNER)
            user = Principal("user@example.com", Role.USER)
            store.assign(owner, "target@example.com", Role.PRO)
            self.assertEqual(store.resolve("target@example.com").role, Role.PRO)
            with self.assertRaises(AuthorizationError):
                store.assign(user, "target@example.com", Role.OWNER)
            restored = RoleStore(path)
            self.assertEqual(restored.resolve("target@example.com").role, Role.PRO)

    def test_require_blocks_privilege_escalation(self) -> None:
        store = RoleStore(Path(tempfile.gettempdir()) / "research-os-rbac-test.json")
        user = Principal("user@example.com", Role.USER)
        store.require(user, Role.USER)
        with self.assertRaises(AuthorizationError):
            store.require(user, Role.PRO)


if __name__ == "__main__":
    unittest.main()
