from __future__ import annotations

import os
import unittest

from identity_providers import get_provider, normalize_account, provider_catalog


class IdentityProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.previous = dict(os.environ)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.previous)

    def test_catalog_exposes_google_microsoft_github(self) -> None:
        ids = {item["id"] for item in provider_catalog()}
        self.assertTrue({"google", "microsoft", "github"}.issubset(ids))

    def test_provider_requires_client_configuration(self) -> None:
        os.environ.pop("RESEARCH_OS_MICROSOFT_CLIENT_ID", None)
        os.environ.pop("RESEARCH_OS_MICROSOFT_CLIENT_SECRET", None)
        provider = get_provider("microsoft")
        self.assertFalse(provider.configured)
        self.assertFalse(provider.available)

    def test_provider_becomes_available_when_configured(self) -> None:
        os.environ["RESEARCH_OS_MICROSOFT_CLIENT_ID"] = "test-client"
        os.environ["RESEARCH_OS_MICROSOFT_CLIENT_SECRET"] = "test-secret"
        self.assertTrue(get_provider("microsoft").available)

    def test_github_identity_normalizes_to_common_principal(self) -> None:
        account = normalize_account(
            "github",
            {"id": 123, "login": "phakphum", "email": "User@Example.com", "name": "Phakphum"},
        )
        self.assertEqual(account["sub"], "123")
        self.assertEqual(account["email"], "user@example.com")
        self.assertEqual(account["name"], "Phakphum")

    def test_oidc_identity_normalizes_to_common_principal(self) -> None:
        account = normalize_account(
            "microsoft",
            {"sub": "abc", "preferred_username": "User@Example.com", "name": "User"},
        )
        self.assertEqual(account["sub"], "abc")
        self.assertEqual(account["email"], "user@example.com")


if __name__ == "__main__":
    unittest.main()
