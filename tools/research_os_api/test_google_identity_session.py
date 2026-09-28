from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import patch

from auth_session import verify_session
from google_identity import GoogleIdentityBroker


class GoogleIdentitySessionTests(unittest.TestCase):
    def test_google_identity_complete_binds_unified_session(self):
        with tempfile.TemporaryDirectory() as data_dir, patch.dict(
            os.environ,
            {
                "RESEARCH_OS_SESSION_SECRET": "test-google-session-secret",
                "RESEARCH_OS_V3_DATA_DIR": data_dir,
            },
            clear=False,
        ), patch.object(
            GoogleIdentityBroker,
            "_with_role",
            side_effect=lambda account: {**account, "role": "USER"},
        ), patch(
            "google_oauth.GoogleOAuthBroker.complete",
            return_value={
                "connected": True,
                "account": {
                    "email": "owner@example.com",
                    "name": "Owner",
                },
                "has_refresh_token": False,
            },
        ):
            result = GoogleIdentityBroker(data_dir).complete(code="test-code", state="test-state")
            self.assertEqual(result["account"]["email"], "owner@example.com")
            self.assertIn("session", result)
            session = verify_session(result["session"])
            self.assertEqual(session["email"], "owner@example.com")
            self.assertEqual(session["role"], "user")

    def test_google_identity_scopes_are_identity_only(self):
        with tempfile.TemporaryDirectory() as data_dir:
            broker = GoogleIdentityBroker(data_dir)
            self.assertEqual(broker._enabled_scopes(), ["email", "openid", "profile"])


if __name__ == "__main__":
    unittest.main()
