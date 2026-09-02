from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from api_auth import OAUTH_HANDOFF_HEADER, extract_session_token
from auth_session import issue_session
from oauth_handoff import consume_handoff, create_handoff


class OAuthHandoffTests(unittest.TestCase):
    def test_handoff_is_single_use(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session = issue_session({"sub": "google-sub", "email": "owner@example.com", "role": "owner"})
            code = create_handoff(root, session, "https://research-os-api.example.com/v1/auth/google/callback", code="oauth-state")

            self.assertEqual(code, "oauth-state")
            self.assertEqual(consume_handoff(root, "oauth-state"), session)
            self.assertIsNone(consume_handoff(root, "oauth-state"))

    def test_auth_guard_resolves_native_oauth_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session = issue_session({"sub": "google-sub", "email": "owner@example.com", "role": "owner"})
            create_handoff(root, session, "https://research-os-api.example.com/v1/auth/google/callback", code="native-state")

            # Patch the broker's data directory so extract_session_token exercises
            # the same production path without contacting Google.
            from google_identity import GoogleIdentityBroker

            original = GoogleIdentityBroker
            class TestBroker(original):
                def __init__(self, data_dir=None):
                    super().__init__(root)

            import api_auth
            previous = api_auth.GoogleIdentityBroker if hasattr(api_auth, "GoogleIdentityBroker") else None
            api_auth.GoogleIdentityBroker = TestBroker
            try:
                self.assertEqual(
                    extract_session_token({OAUTH_HANDOFF_HEADER: "native-state"}),
                    session,
                )
            finally:
                if previous is None:
                    delattr(api_auth, "GoogleIdentityBroker")
                else:
                    api_auth.GoogleIdentityBroker = previous


if __name__ == "__main__":
    unittest.main()
