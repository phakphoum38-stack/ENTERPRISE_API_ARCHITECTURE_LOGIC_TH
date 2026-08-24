import os
import unittest

from tools.research_os_api.api_auth import require_session
from tools.research_os_api.auth_session import issue_session


class ResearchOSApiAuthBoundaryTests(unittest.TestCase):
    def setUp(self):
        self._old = os.environ.get("RESEARCH_OS_SESSION_SECRET")
        os.environ["RESEARCH_OS_SESSION_SECRET"] = "test-only-p0-002-secret"

    def tearDown(self):
        if self._old is None:
            os.environ.pop("RESEARCH_OS_SESSION_SECRET", None)
        else:
            os.environ["RESEARCH_OS_SESSION_SECRET"] = self._old

    def test_verified_session_can_be_resolved_from_header(self):
        token = issue_session({"sub": "user-a", "email": "a@example.test", "role": "user"})
        principal = require_session({"X-Research-OS-Session": token})
        self.assertEqual(principal["user_id"], "user-a")
        self.assertEqual(principal["email"], "a@example.test")
        self.assertEqual(principal["role"], "user")

    def test_verified_session_can_be_resolved_from_cookie(self):
        token = issue_session({"sub": "user-b", "email": "b@example.test", "role": "pro"})
        principal = require_session({"Cookie": f"research_os_session={token}; other=x"})
        self.assertEqual(principal["user_id"], "user-b")
        self.assertEqual(principal["role"], "pro")

    def test_client_identity_fields_are_not_accepted_as_authentication(self):
        with self.assertRaises(ValueError):
            require_session({"X-Research-OS-User-ID": "owner", "X-Research-OS-Role": "owner"})

    def test_tampered_session_is_rejected(self):
        token = issue_session({"sub": "user-a", "email": "a@example.test", "role": "user"})
        body, signature = token.split(".", 1)
        tampered = body[:-1] + ("A" if body[-1] != "A" else "B") + "." + signature
        with self.assertRaises(ValueError):
            require_session({"X-Research-OS-Session": tampered})


if __name__ == "__main__":
    unittest.main()
