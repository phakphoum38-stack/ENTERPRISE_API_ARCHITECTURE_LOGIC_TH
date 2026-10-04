from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import patch

from auth_session import issue_session, revoke_all_sessions, revoke_session, verify_session
from session_registry import get_session, list_sessions


class PlatformSessionRegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.patch = patch.dict(
            os.environ,
            {
                "RESEARCH_OS_SESSION_SECRET": "test-platform-session-secret",
                "RESEARCH_OS_V3_DATA_DIR": self.tmp.name,
            },
            clear=False,
        )
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def test_multiple_sessions_are_registered_without_tokens(self):
        first = issue_session(
            {"user_id": "google:alice", "email": "alice@example.test", "role": "USER", "provider": "google"}
        )
        second = issue_session(
            {"user_id": "google:alice", "email": "alice@example.test", "role": "USER", "provider": "google"}
        )
        records = list_sessions("google:alice")
        self.assertEqual({item["session_id"] for item in records}, {
            verify_session(first)["session_id"],
            verify_session(second)["session_id"],
        })
        for item in records:
            self.assertNotIn("token", item)
            self.assertNotIn("access_token", item)
            self.assertEqual(item["provider"], "google")
            self.assertEqual(item["user_id"], "google:alice")

    def test_registry_isolation_prevents_cross_user_listing(self):
        issue_session({"user_id": "alice", "email": "alice@example.test", "role": "USER"})
        issue_session({"user_id": "bob", "email": "bob@example.test", "role": "USER"})
        self.assertEqual(len(list_sessions("alice")), 1)
        self.assertEqual(len(list_sessions("bob")), 1)
        self.assertIsNone(get_session("alice", "bob-session"))

    def test_revoke_one_updates_registry_and_preserves_other_session(self):
        first = issue_session({"user_id": "alice", "email": "alice@example.test", "role": "USER"})
        second = issue_session({"user_id": "alice", "email": "alice@example.test", "role": "USER"})
        first_id = verify_session(first)["session_id"]
        second_id = verify_session(second)["session_id"]

        revoke_session(first)

        self.assertEqual([item["session_id"] for item in list_sessions("alice")], [second_id])
        revoked = get_session("alice", first_id)
        self.assertTrue(revoked["revoked"])

    def test_revoke_all_updates_only_target_user(self):
        issue_session({"user_id": "alice", "email": "alice@example.test", "role": "USER"})
        issue_session({"user_id": "alice", "email": "alice@example.test", "role": "USER"})
        issue_session({"user_id": "bob", "email": "bob@example.test", "role": "USER"})

        revoke_all_sessions("alice")

        self.assertEqual(list_sessions("alice"), [])
        self.assertEqual(len(list_sessions("bob")), 1)
        self.assertEqual(
            len([item for item in list_sessions("alice", include_revoked=True) if item["revoked"]]),
            2,
        )

    def test_expired_registry_sessions_are_not_active(self):
        token = issue_session(
            {"user_id": "alice", "email": "alice@example.test", "role": "USER"},
            ttl_seconds=60,
        )
        session = verify_session(token)
        from session_registry import _load, _save

        records = _load("alice")
        records[0]["expires_at"] = 1
        _save("alice", records)
        self.assertEqual(list_sessions("alice"), [])
        self.assertEqual(get_session("alice", session["session_id"])["session_id"], session["session_id"])


if __name__ == "__main__":
    unittest.main()
