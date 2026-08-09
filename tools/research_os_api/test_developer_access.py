from __future__ import annotations

import tempfile
import unittest

from developer_access import DeveloperAccessStore


class DeveloperAccessStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.store = DeveloperAccessStore(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _request(self) -> dict:
        return self.store.request_access(
            developer_id="dev:alice",
            owner_id="user:owner",
            workspace_id="workspace-1",
            resource_id="file-1",
            resource_name="Owned document.md",
            requested_scopes=["read", "write"],
            purpose="Fix and test the owner's project file",
        )

    def test_developer_has_no_access_before_owner_approval(self) -> None:
        self._request()
        decision = self.store.authorize(
            principal_id="dev:alice",
            owner_id="user:owner",
            workspace_id="workspace-1",
            resource_id="file-1",
            scope="read",
        )
        self.assertFalse(decision["allowed"])
        self.assertTrue(decision["owner_access_unchanged"])

    def test_only_owner_can_approve_and_owner_access_never_changes(self) -> None:
        request = self._request()
        with self.assertRaises(PermissionError):
            self.store.approve_request(
                owner_id="user:someone-else",
                request_id=request["request_id"],
            )

        grant = self.store.approve_request(
            owner_id="user:owner",
            request_id=request["request_id"],
            scopes=["read"],
            expires_in_seconds=3600,
        )
        self.assertEqual(grant["scopes"], ["read"])
        self.assertTrue(grant["owner_access_unchanged"])

        owner = self.store.authorize(
            principal_id="user:owner",
            owner_id="user:owner",
            workspace_id="workspace-1",
            resource_id="file-1",
            scope="write",
        )
        self.assertTrue(owner["allowed"])
        self.assertEqual(owner["mode"], "owner")
        self.assertTrue(owner["owner_access_unchanged"])

        developer_read = self.store.authorize(
            principal_id="dev:alice",
            owner_id="user:owner",
            workspace_id="workspace-1",
            resource_id="file-1",
            scope="read",
        )
        self.assertTrue(developer_read["allowed"])
        self.assertEqual(developer_read["mode"], "developer_grant")

        developer_write = self.store.authorize(
            principal_id="dev:alice",
            owner_id="user:owner",
            workspace_id="workspace-1",
            resource_id="file-1",
            scope="write",
        )
        self.assertFalse(developer_write["allowed"])

    def test_owner_can_list_and_revoke_active_grants(self) -> None:
        request = self._request()
        grant = self.store.approve_request(
            owner_id="user:owner",
            request_id=request["request_id"],
            scopes=["read"],
            expires_in_seconds=3600,
        )
        owner_grants = self.store.list_owner_grants("user:owner")
        self.assertEqual([item["grant_id"] for item in owner_grants], [grant["grant_id"]])
        self.assertTrue(owner_grants[0]["active"])
        self.assertTrue(owner_grants[0]["owner_access_unchanged"])

        self.store.revoke_grant(
            owner_id="user:owner",
            grant_id=grant["grant_id"],
            reason="Owner revoked access",
        )
        self.assertEqual(self.store.list_owner_grants("user:owner"), [])
        historical = self.store.list_owner_grants("user:owner", active_only=False)
        self.assertEqual(len(historical), 1)
        self.assertFalse(historical[0]["active"])

    def test_owner_can_revoke_developer_immediately(self) -> None:
        request = self._request()
        grant = self.store.approve_request(
            owner_id="user:owner",
            request_id=request["request_id"],
        )
        before = self.store.authorize(
            principal_id="dev:alice",
            owner_id="user:owner",
            workspace_id="workspace-1",
            resource_id="file-1",
            scope="write",
        )
        self.assertTrue(before["allowed"])

        revoked = self.store.revoke_grant(
            owner_id="user:owner",
            grant_id=grant["grant_id"],
            reason="Work completed",
        )
        self.assertFalse(revoked["active"])

        after = self.store.authorize(
            principal_id="dev:alice",
            owner_id="user:owner",
            workspace_id="workspace-1",
            resource_id="file-1",
            scope="write",
        )
        self.assertFalse(after["allowed"])

        owner = self.store.authorize(
            principal_id="user:owner",
            owner_id="user:owner",
            workspace_id="workspace-1",
            resource_id="file-1",
            scope="write",
        )
        self.assertTrue(owner["allowed"])

    def test_state_survives_restart(self) -> None:
        request = self._request()
        self.store.approve_request(
            owner_id="user:owner",
            request_id=request["request_id"],
            scopes=["read"],
        )
        reloaded = DeveloperAccessStore(self.temp.name)
        grants = reloaded.list_developer_grants("dev:alice")
        self.assertEqual(len(grants), 1)
        self.assertTrue(grants[0]["active"])
        self.assertTrue(grants[0]["owner_access_unchanged"])


if __name__ == "__main__":
    unittest.main()
