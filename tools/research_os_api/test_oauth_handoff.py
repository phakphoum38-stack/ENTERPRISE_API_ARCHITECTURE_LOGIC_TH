from __future__ import annotations

import os
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
            os.environ["RESEARCH_OS_DATA_DIR"] = directory
            try:
                root = Path(directory) / "google_workspace"
                root.mkdir(parents=True, exist_ok=True)
                session = issue_session({"sub": "google-sub", "email": "owner@example.com", "role": "owner"})
                create_handoff(root, session, "https://research-os-api.example.com/v1/auth/google/callback", code="native-state")

                self.assertEqual(
                    extract_session_token({OAUTH_HANDOFF_HEADER: "native-state"}),
                    session,
                )
            finally:
                os.environ.pop("RESEARCH_OS_DATA_DIR", None)


if __name__ == "__main__":
    unittest.main()
