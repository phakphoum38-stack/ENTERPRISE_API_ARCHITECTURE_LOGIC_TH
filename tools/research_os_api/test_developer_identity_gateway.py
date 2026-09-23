from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from developer_identity import IdentityAssertionError, IdentityAssertionVerifier
from developer_identity_gateway import mint_developer_assertion


class DeveloperIdentityGatewayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.secret = "gateway-secret-0123456789"
        self.session = {
            "user_id": "owner-user-123",
            "email": "owner@example.test",
            "role": "owner",
            "session_id": "session-abc",
        }

    def test_mints_assertion_from_verified_session(self) -> None:
        with patch.dict(os.environ, {"RESEARCH_OS_IDENTITY_PROXY_SECRET": self.secret}):
            result = mint_developer_assertion(self.session, now=1000)

        self.assertEqual(result["principal"], "owner-user-123")
        self.assertEqual(result["email"], "owner@example.test")
        self.assertEqual(result["role"], "owner")
        self.assertEqual(result["expires_at"], 1120)

        verifier = IdentityAssertionVerifier(self.secret)
        identity = verifier.verify(result["headers"], now=1050)
        self.assertEqual(identity.principal, "owner-user-123")

    def test_client_cannot_override_principal(self) -> None:
        session = {**self.session, "principal": "attacker@example.test"}
        with patch.dict(os.environ, {"RESEARCH_OS_IDENTITY_PROXY_SECRET": self.secret}):
            result = mint_developer_assertion(session, now=1000)
        self.assertEqual(result["principal"], "owner-user-123")
        self.assertEqual(result["headers"]["X-ResearchOS-Principal"], "owner-user-123")

    def test_missing_gateway_secret_fails_closed(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(IdentityAssertionError, "not configured"):
                mint_developer_assertion(self.session, now=1000)

    def test_incomplete_verified_session_fails_closed(self) -> None:
        with patch.dict(os.environ, {"RESEARCH_OS_IDENTITY_PROXY_SECRET": self.secret}):
            with self.assertRaisesRegex(IdentityAssertionError, "incomplete"):
                mint_developer_assertion({**self.session, "user_id": ""}, now=1000)


if __name__ == "__main__":
    unittest.main()
