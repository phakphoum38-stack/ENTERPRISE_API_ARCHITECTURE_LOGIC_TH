from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import email_identity


class EmailIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.env = patch.dict(
            os.environ,
            {
                "RESEARCH_OS_DATA_DIR": self.temp.name,
                "RESEARCH_OS_IDENTITY_SECRET": "test-secret-that-is-longer-than-32-characters",
                "RESEARCH_OS_SMTP_HOST": "smtp.example.test",
                "RESEARCH_OS_SMTP_FROM": "research-os@example.test",
            },
            clear=False,
        )
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_request_verify_and_profile(self) -> None:
        captured: dict[str, str] = {}

        def capture(email: str, code: str) -> None:
            captured["email"] = email
            captured["code"] = code

        with patch.object(email_identity, "_send_code", side_effect=capture):
            challenge = email_identity.request_code("Owner@Example.com")

        self.assertEqual(captured["email"], "owner@example.com")
        self.assertEqual(len(captured["code"]), 6)
        verified = email_identity.verify_code(
            challenge["challenge_id"],
            captured["code"],
        )
        self.assertEqual(verified["profile"]["email"], "owner@example.com")
        self.assertGreater(verified["expires_at"], 0)

        profile = email_identity.get_profile(f"Bearer {verified['token']}")
        self.assertEqual(profile["email"], "owner@example.com")
        self.assertFalse(profile["private_sync"])

    def test_invalid_code_does_not_create_session(self) -> None:
        with patch.object(email_identity, "_send_code"):
            challenge = email_identity.request_code("owner@example.com")
        with self.assertRaises(ValueError):
            email_identity.verify_code(challenge["challenge_id"], "000000")

    def test_preferences_are_allow_listed(self) -> None:
        captured: dict[str, str] = {}
        with patch.object(
            email_identity,
            "_send_code",
            side_effect=lambda email, code: captured.update(code=code),
        ):
            challenge = email_identity.request_code("owner@example.com")
        verified = email_identity.verify_code(challenge["challenge_id"], captured["code"])
        result = email_identity.update_preferences(
            f"Bearer {verified['token']}",
            {
                "theme": "dark",
                "api_auto_discovery": True,
                "heartbeat_seconds": 20,
                "private_context": "must-not-sync",
                "provider_api_key": "must-not-sync",
            },
        )
        self.assertEqual(result["preferences"]["theme"], "dark")
        self.assertNotIn("private_context", result["preferences"])
        self.assertNotIn("provider_api_key", result["preferences"])

    def test_identity_state_uses_configured_data_directory(self) -> None:
        with patch.object(email_identity, "_send_code"):
            email_identity.request_code("owner@example.com")
        expected = Path(self.temp.name) / "identity" / "email_identity.json"
        self.assertTrue(expected.is_file())


if __name__ == "__main__":
    unittest.main()
