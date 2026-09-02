from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from identity_providers import get_provider, normalize_account, provider_catalog
from multi_login import STATE_TTL_SECONDS, begin_login, normalize_callback


class MultiLoginTests(unittest.TestCase):
    def test_catalog_contains_supported_providers_without_exposing_secrets(self):
        catalog = provider_catalog()
        names = {item["id"] for item in catalog}
        self.assertTrue({"google", "microsoft", "github"}.issubset(names))
        self.assertNotIn("client_secret", catalog[0])

    def test_begin_login_requires_configuration(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(Exception):
                begin_login("google", redirect_uri="http://127.0.0.1/callback")

    def test_begin_login_generates_state_and_provider_url(self):
        with patch.dict(
            os.environ,
            {
                "RESEARCH_OS_GOOGLE_CLIENT_ID": "test-client",
                "RESEARCH_OS_GOOGLE_CLIENT_SECRET": "test-secret",
            },
            clear=False,
        ):
            state, url = begin_login("google", redirect_uri="http://127.0.0.1/callback")
        self.assertEqual(state.provider, "google")
        self.assertTrue(state.state)
        self.assertTrue(state.valid())
        self.assertIn("accounts.google.com", url)
        self.assertNotIn("test-secret", url)
        self.assertLessEqual(STATE_TTL_SECONDS, 600)

    def test_normalize_google_identity(self):
        value = normalize_callback(
            "google",
            {"sub": "google-user", "email": "User@Example.com", "name": "User"},
        )
        self.assertEqual(value["provider"], "google")
        self.assertEqual(value["sub"], "google-user")
        self.assertEqual(value["email"], "user@example.com")

    def test_normalize_github_identity(self):
        value = normalize_account(
            "github",
            {"id": 123, "email": "Dev@Example.com", "login": "dev", "name": "Dev"},
        )
        self.assertEqual(value["sub"], "123")
        self.assertEqual(value["email"], "dev@example.com")
        self.assertEqual(value["login"], "dev")

    def test_unknown_provider_is_rejected(self):
        with self.assertRaises(ValueError):
            get_provider("unknown")


if __name__ == "__main__":
    unittest.main()
