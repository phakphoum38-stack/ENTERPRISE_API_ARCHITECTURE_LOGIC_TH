from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from api_auth import OAUTH_HANDOFF_HEADER, extract_session_token
from auth_session import issue_session, revoke_session, verify_session
from oauth_handoff import consume_handoff, create_handoff


class OAuthHandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        self._previous_session_secret = os.environ.get("RESEARCH_OS_SESSION_SECRET")
        self._previous_data_dir = os.environ.get("RESEARCH_OS_V3_DATA_DIR")
        os.environ["RESEARCH_OS_SESSION_SECRET"] = "ci-oauth-handoff-test-secret"

    def tearDown(self) -> None:
        if self._previous_session_secret is None:
            os.environ.pop("RESEARCH_OS_SESSION_SECRET", None)
        else:
            os.environ["RESEARCH_OS_SESSION_SECRET"] = self._previous_session_secret
        if self._previous_data_dir is None:
            os.environ.pop("RESEARCH_OS_V3_DATA_DIR", None)
        else:
            os.environ["RESEARCH_OS_V3_DATA_DIR"] = self._previous_data_dir

    def test_handoff_is_single_use_and_rotates_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            os.environ["RESEARCH_OS_V3_DATA_DIR"] = directory
            root = Path(directory) / "google_workspace"
            session = issue_session({"sub": "google-sub", "email": "owner@example.com", "role": "owner"})
            code = create_handoff(
                root,
                session,
                "https://research-os-api.example.com/v1/auth/google/callback",
                code="oauth-state",
            )

            self.assertEqual(code, "oauth-state")
            rotated = consume_handoff(root, "oauth-state")
            self.assertIsNotNone(rotated)
            self.assertNotEqual(rotated, session)
            self.assertEqual(verify_session(rotated)["email"], "owner@example.com")
            self.assertIsNone(consume_handoff(root, "oauth-state"))

    def test_handoff_store_never_contains_session_bearer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            os.environ["RESEARCH_OS_V3_DATA_DIR"] = directory
            root = Path(directory)
            session = issue_session({"sub": "google-sub", "email": "owner@example.com", "role": "owner"})
            create_handoff(root, session, "https://example.test/callback", code="state-secret")
            stored = (root / "oauth_handoffs.json").read_text(encoding="utf-8")
            self.assertNotIn(session, stored)
            self.assertNotIn("state-secret", stored)

    def test_revoked_source_session_cannot_be_handed_off(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            os.environ["RESEARCH_OS_V3_DATA_DIR"] = directory
            root = Path(directory)
            session = issue_session({"sub": "google-sub", "email": "owner@example.com", "role": "owner"})
            create_handoff(root, session, "https://example.test/callback", code="revoked-state")
            revoke_session(session)
            self.assertIsNone(consume_handoff(root, "revoked-state"))

    def test_redirect_and_audience_are_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            os.environ["RESEARCH_OS_V3_DATA_DIR"] = directory
            root = Path(directory)
            session = issue_session({"sub": "google-sub", "email": "owner@example.com", "role": "owner"})
            create_handoff(
                root,
                session,
                "https://example.test/callback",
                code="bound-state",
                audience="research-os-native",
            )
            self.assertIsNone(
                consume_handoff(
                    root,
                    "bound-state",
                    expected_redirect_uri="https://attacker.example/callback",
                    expected_audience="research-os-native",
                )
            )

    def test_auth_guard_resolves_native_oauth_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            os.environ["RESEARCH_OS_V3_DATA_DIR"] = directory
            root = Path(directory) / "google_workspace"
            session = issue_session({"sub": "google-sub", "email": "owner@example.com", "role": "owner"})
            create_handoff(
                root,
                session,
                "https://research-os-api.example.com/v1/auth/google/callback",
                code="native-state",
            )

            resolved = extract_session_token({OAUTH_HANDOFF_HEADER: "native-state"})
            self.assertIsNotNone(resolved)
            self.assertNotEqual(resolved, session)
            self.assertEqual(verify_session(resolved)["user_id"], "google-sub")


if __name__ == "__main__":
    unittest.main()
