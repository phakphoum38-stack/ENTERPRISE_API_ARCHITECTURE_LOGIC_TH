import os
import unittest
from unittest.mock import patch

import multi_login_runtime


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


if __name__ == "__main__":
    unittest.main()
