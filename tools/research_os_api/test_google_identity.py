import os
import tempfile
import unittest
from unittest.mock import patch

from google_identity import GoogleIdentityBroker


class GoogleIdentityBrokerTest(unittest.TestCase):
    def test_identity_sign_in_uses_only_identity_scopes(self):
        env = {
            "RESEARCH_OS_GOOGLE_CLIENT_ID": "client-id.apps.googleusercontent.com",
            "RESEARCH_OS_GOOGLE_CLIENT_SECRET": "client-secret",
            "RESEARCH_OS_API_PORT": "8787",
        }
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, env, clear=True):
            broker = GoogleIdentityBroker(tmp)
            payload = broker.begin()
            url = payload["authorization_url"]
            self.assertIn("openid", url)
            self.assertIn("email", url)
            self.assertIn("profile", url)
            self.assertNotIn("gmail.modify", url)
            self.assertNotIn("spreadsheets", url)
            self.assertNotIn("calendar", url)
            self.assertIn("127.0.0.1%3A8787%2Fv1%2Fauth%2Fgoogle%2Fcallback", url)

    def test_render_external_url_becomes_mobile_callback(self):
        env = {
            "RESEARCH_OS_GOOGLE_CLIENT_ID": "client-id.apps.googleusercontent.com",
            "RESEARCH_OS_GOOGLE_CLIENT_SECRET": "client-secret",
            "RENDER_EXTERNAL_URL": "https://research-os-api.example.com/",
        }
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, env, clear=True):
            broker = GoogleIdentityBroker(tmp)
            self.assertEqual(
                broker.redirect_uri(),
                "https://research-os-api.example.com/v1/auth/google/callback",
            )

    def test_explicit_identity_redirect_wins(self):
        env = {
            "RESEARCH_OS_GOOGLE_CLIENT_ID": "client-id.apps.googleusercontent.com",
            "RESEARCH_OS_GOOGLE_CLIENT_SECRET": "client-secret",
            "RENDER_EXTERNAL_URL": "https://research-os-api.example.com",
            "RESEARCH_OS_GOOGLE_IDENTITY_REDIRECT_URI": "https://auth.example.net/google/callback",
        }
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, env, clear=True):
            broker = GoogleIdentityBroker(tmp)
            self.assertEqual(
                broker.redirect_uri(),
                "https://auth.example.net/google/callback",
            )


if __name__ == "__main__":
    unittest.main()
