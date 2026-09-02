import os
import unittest
from unittest.mock import patch

import multi_login_runtime
from auth_session import clear_cookie_header, issue_session, verify_session
from server_auth_routes import auth_status, auth_signout


class MultiLoginRuntimeTests(unittest.TestCase):
    def test_begin_requires_available_provider(self):
        with patch.dict(os.environ, {"RESEARCH_OS_GOOGLE_CLIENT_ID": "client", "RESEARCH_OS_GOOGLE_CLIENT_SECRET": "secret"}, clear=False):
            state, url = multi_login_runtime.begin_runtime_login("google", "http://127.0.0.1:8787/v1/auth/google/callback")
        self.assertTrue(state)
        self.assertIn("accounts.google.com", url)
        self.assertNotIn("secret", url)

    def test_github_email_selection_prefers_verified_primary(self):
        payload = [
            {"email": "other@example.com", "verified": True, "primary": False},
            {"email": "primary@example.com", "verified": True, "primary": True},
            {"email": "unverified@example.com", "verified": False, "primary": False},
        ]
        with patch.object(multi_login_runtime, "_get_json", return_value=payload):
            self.assertEqual(multi_login_runtime._github_verified_email("token"), "primary@example.com")

    def test_expired_state_rejected(self):
        with patch.dict(os.environ, {"RESEARCH_OS_GOOGLE_CLIENT_ID": "client", "RESEARCH_OS_GOOGLE_CLIENT_SECRET": "secret"}, clear=False):
            state, _ = multi_login_runtime.begin_runtime_login("google", "http://127.0.0.1:8787/v1/auth/google/callback")
        pending = multi_login_runtime._PENDING[state]
        pending.created_at -= multi_login_runtime.STATE_TTL_SECONDS + 1
        with self.assertRaises(multi_login_runtime.MultiLoginRuntimeError):
            multi_login_runtime.complete_runtime_login("code", state)

    def test_unified_status_and_signout(self):
        with patch.dict(os.environ, {"RESEARCH_OS_SESSION_SECRET": "test-secret"}, clear=False):
            token = issue_session({"user_id": "google:123", "email": "user@example.com", "role": "USER"})
            self.assertTrue(auth_status(f"research_os_session={token}")["connected"])
            cookie = auth_signout(f"research_os_session={token}")
            self.assertIn("Max-Age=0", cookie)
            with self.assertRaises(ValueError):
                verify_session(token)


if __name__ == "__main__":
    unittest.main()
