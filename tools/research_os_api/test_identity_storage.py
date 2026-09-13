from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from auth_session import SessionRevocationStore, issue_session, verify_session
from identity_storage import storage_key


class IdentityStorageTests(unittest.TestCase):
    def test_storage_key_is_deterministic_and_filesystem_safe(self):
        for user_id in ("google:123", "email:abc:def", "owner@example.com", "a/b", ".."):
            key = storage_key(user_id)
            self.assertTrue(key.startswith("u_"))
            self.assertRegex(key, r"^u_[0-9a-f]{64}$")
            self.assertNotIn(":", key)
            self.assertNotIn("/", key)
            self.assertNotIn("\\", key)
            self.assertEqual(key, storage_key(user_id))

    def test_storage_key_does_not_rewrite_canonical_identity(self):
        canonical = "google:123"
        self.assertNotEqual(storage_key(canonical), storage_key(" google:123 "))
        with self.assertRaisesRegex(ValueError, "canonical"):
            storage_key(" google:123 ")

    def test_session_revocation_works_for_windows_invalid_identity(self):
        with tempfile.TemporaryDirectory() as data_dir, patch.dict(
            os.environ,
            {
                "RESEARCH_OS_SESSION_SECRET": "test-storage-secret",
                "RESEARCH_OS_V3_DATA_DIR": data_dir,
            },
            clear=False,
        ):
            user_id = "google:123"
            token = issue_session({"user_id": user_id, "email": "owner@example.com"})
            payload = verify_session(token)
            self.assertEqual(payload["user_id"], user_id)
            SessionRevocationStore().revoke(user_id, payload["session_id"])
            with self.assertRaisesRegex(ValueError, "session revoked"):
                verify_session(token)
            user_dirs = list((Path(data_dir) / "users").iterdir())
            self.assertEqual(len(user_dirs), 1)
            self.assertRegex(user_dirs[0].name, r"^u_[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
