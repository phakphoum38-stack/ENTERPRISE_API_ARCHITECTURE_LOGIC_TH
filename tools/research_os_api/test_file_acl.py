from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from file_acl import ACLAuthorizationError, FileACLStore


class FileACLTests(unittest.TestCase):
    def test_owner_can_read_write_share_and_transfer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FileACLStore(Path(tmp) / "acl.json")
            store.create("file-1", "owner@example.com")
            self.assertTrue(store.authorize("file-1", "owner@example.com", "write"))
            store.share("file-1", "owner@example.com", "user@example.com")
            self.assertTrue(store.authorize("file-1", "user@example.com", "read"))
            self.assertFalse(store.authorize("file-1", "user@example.com", "write"))
            store.transfer("file-1", "owner@example.com", "new-owner@example.com")
            self.assertTrue(store.authorize("file-1", "new-owner@example.com", "delete"))

    def test_non_owner_cannot_share_revoke_or_transfer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FileACLStore(Path(tmp) / "acl.json")
            store.create("file-2", "owner@example.com")
            store.share("file-2", "owner@example.com", "user@example.com")
            for action in ("share", "revoke", "transfer"):
                with self.assertRaises(ACLAuthorizationError):
                    if action == "share":
                        store.share("file-2", "user@example.com", "other@example.com")
                    elif action == "revoke":
                        store.revoke("file-2", "user@example.com", "owner@example.com")
                    else:
                        store.transfer("file-2", "user@example.com", "other@example.com")

    def test_missing_resource_is_denied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FileACLStore(Path(tmp) / "acl.json")
            with self.assertRaises(ACLAuthorizationError):
                store.authorize("missing", "user@example.com", "read")


if __name__ == "__main__":
    unittest.main()
