import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_DIR = ROOT / "tools" / "research_os_api"
sys.path.insert(0, str(API_DIR))

import auth_session  # noqa: E402


class ResearchOSSessionRevocationTests(unittest.TestCase):
    def setUp(self):
        self.previous_secret = os.environ.get("RESEARCH_OS_SESSION_SECRET")
        os.environ["RESEARCH_OS_SESSION_SECRET"] = "test-only-research-os-session-secret"
        self.tmp = tempfile.TemporaryDirectory()
        self.previous_data_dir = os.environ.get("RESEARCH_OS_V3_DATA_DIR")
        os.environ["RESEARCH_OS_V3_DATA_DIR"] = self.tmp.name

    def tearDown(self):
        if self.previous_secret is None:
            os.environ.pop("RESEARCH_OS_SESSION_SECRET", None)
        else:
            os.environ["RESEARCH_OS_SESSION_SECRET"] = self.previous_secret
        if self.previous_data_dir is None:
            os.environ.pop("RESEARCH_OS_V3_DATA_DIR", None)
        else:
            os.environ["RESEARCH_OS_V3_DATA_DIR"] = self.previous_data_dir
        self.tmp.cleanup()

    def test_revoked_session_is_rejected_while_other_user_remains_valid(self):
        alice = auth_session.issue_session({"email": "alice@example.test", "sub": "alice", "role": "user"})
        bob = auth_session.issue_session({"email": "bob@example.test", "sub": "bob", "role": "user"})

        auth_session.revoke_session(alice)

        with self.assertRaises(ValueError):
            auth_session.verify_session(alice)
        self.assertEqual(auth_session.verify_session(bob)["user_id"], "bob")

    def test_revoke_all_sessions_invalidates_only_target_user(self):
        alice_a = auth_session.issue_session({"email": "alice@example.test", "sub": "alice", "role": "user"})
        alice_b = auth_session.issue_session({"email": "alice@example.test", "sub": "alice", "role": "user"})
        bob = auth_session.issue_session({"email": "bob@example.test", "sub": "bob", "role": "user"})

        auth_session.revoke_all_sessions("alice")

        for token in (alice_a, alice_b):
            with self.assertRaises(ValueError):
                auth_session.verify_session(token)
        self.assertEqual(auth_session.verify_session(bob)["user_id"], "bob")

    def test_revocation_survives_process_boundary(self):
        token = auth_session.issue_session({"email": "alice@example.test", "sub": "alice", "role": "user"})
        auth_session.revoke_session(token)

        # Re-read the durable state through a fresh store instance.
        store = auth_session.SessionRevocationStore()
        self.assertTrue(store.is_revoked(auth_session.session_id(token), "alice"))


if __name__ == "__main__":
    unittest.main()
