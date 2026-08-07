import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from google_oauth import GoogleOAuthBroker, GoogleOAuthError


class GoogleOAuthBrokerTest(unittest.TestCase):
    def test_begin_requires_backend_credentials(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(GoogleOAuthError):
                GoogleOAuthBroker(tmp).begin()

    def test_begin_builds_google_authorization_url_without_exposing_secret(self):
        env = {
            "RESEARCH_OS_GOOGLE_CLIENT_ID": "client-id.apps.googleusercontent.com",
            "RESEARCH_OS_GOOGLE_CLIENT_SECRET": "super-secret",
            "RESEARCH_OS_API_PORT": "8787",
        }
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, env, clear=True):
            broker = GoogleOAuthBroker(tmp)
            payload = broker.begin()
            url = payload["authorization_url"]
            self.assertIn("accounts.google.com/o/oauth2/v2/auth", url)
            self.assertIn("client-id.apps.googleusercontent.com", url)
            self.assertNotIn("super-secret", url)
            self.assertIn("127.0.0.1%3A8787", url)
            self.assertTrue((Path(tmp) / "google_workspace" / "oauth_state.json").exists())

    def test_status_and_disconnect_use_backend_token_store(self):
        env = {
            "RESEARCH_OS_GOOGLE_CLIENT_ID": "client-id",
            "RESEARCH_OS_GOOGLE_CLIENT_SECRET": "client-secret",
        }
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, env, clear=True):
            broker = GoogleOAuthBroker(tmp)
            self.assertFalse(broker.status()["connected"])
            broker.token_path.write_text(json.dumps({"refresh_token": "refresh"}), encoding="utf-8")
            self.assertTrue(broker.status()["connected"])
            result = broker.disconnect()
            self.assertTrue(result["disconnected"])
            self.assertFalse(broker.token_path.exists())


if __name__ == "__main__":
    unittest.main()
