import os
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_DIR = ROOT / "tools" / "research_os_api"
sys.path.insert(0, str(API_DIR))

import auth_session  # noqa: E402


class ResearchOSAuthSessionTests(unittest.TestCase):
    def setUp(self):
        self.previous = os.environ.get("RESEARCH_OS_SESSION_SECRET")
        os.environ["RESEARCH_OS_SESSION_SECRET"] = "test-only-research-os-session-secret"

    def tearDown(self):
        if self.previous is None:
            os.environ.pop("RESEARCH_OS_SESSION_SECRET", None)
        else:
            os.environ["RESEARCH_OS_SESSION_SECRET"] = self.previous

    def test_each_identity_gets_distinct_signed_session(self):
        a = auth_session.issue_session({"email": "a@example.test", "sub": "user-a", "role": "user"})
        b = auth_session.issue_session({"email": "b@example.test", "sub": "user-b", "role": "pro"})
        self.assertNotEqual(a, b)
        self.assertEqual(auth_session.verify_session(a)["user_id"], "user-a")
        self.assertEqual(auth_session.verify_session(b)["user_id"], "user-b")
        self.assertEqual(auth_session.verify_session(b)["role"], "pro")

    def test_tampering_is_rejected(self):
        token = auth_session.issue_session({"email": "a@example.test", "sub": "user-a", "role": "user"})
        body, sig = token.split(".", 1)
        tampered = body[:-1] + ("A" if body[-1] != "A" else "B") + "." + sig
        with self.assertRaises(ValueError):
            auth_session.verify_session(tampered)

    def test_expired_session_is_rejected(self):
        token = auth_session.issue_session(
            {"email": "a@example.test", "sub": "user-a", "role": "user"},
            ttl_seconds=60,
        )
        payload = auth_session.verify_session(token)
        payload["exp"] = int(time.time()) - 1
        body = auth_session._encode(payload)
        with self.assertRaises(ValueError):
            auth_session.verify_session(body)

    def test_missing_secret_fails_closed(self):
        os.environ.pop("RESEARCH_OS_SESSION_SECRET", None)
        with self.assertRaises(RuntimeError):
            auth_session.issue_session({"email": "a@example.test", "sub": "user-a"})


if __name__ == "__main__":
    unittest.main()
