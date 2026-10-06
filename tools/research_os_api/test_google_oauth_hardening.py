from __future__ import annotations

import base64
import json
import os
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from google_oauth import GoogleOAuthBroker, GoogleOAuthError, _b64url_decode


class GoogleOAuthHardeningTests(unittest.TestCase):
    def test_begin_binds_pkce_nonce_and_backend_state(self) -> None:
        previous = {
            key: os.environ.get(key)
            for key in ("RESEARCH_OS_GOOGLE_CLIENT_ID", "RESEARCH_OS_GOOGLE_CLIENT_SECRET")
        }
        os.environ["RESEARCH_OS_GOOGLE_CLIENT_ID"] = "test-client.apps.googleusercontent.com"
        os.environ["RESEARCH_OS_GOOGLE_CLIENT_SECRET"] = "server-only-secret"
        try:
            with tempfile.TemporaryDirectory() as tmp:
                broker = GoogleOAuthBroker(Path(tmp))
                result = broker.begin()
                query = parse_qs(urlsplit(result["authorization_url"]).query)
                state = json.loads(broker.state_path.read_text(encoding="utf-8"))

                self.assertEqual(query["client_id"], ["test-client.apps.googleusercontent.com"])
                self.assertEqual(query["code_challenge_method"], ["S256"])
                self.assertEqual(query["code_challenge"], [state["code_challenge"]])
                self.assertEqual(query["nonce"], [state["nonce"]])
                self.assertNotIn("client_secret", query)
                self.assertEqual(state["redirect_uri"], result["redirect_uri"])
                self.assertEqual(len(state["code_verifier"]), 43)
                self.assertEqual(result["pkce"], "S256")
                self.assertTrue(result["nonce_created"])
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_state_requires_pkce_and_nonce_material(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            broker = GoogleOAuthBroker(Path(tmp))
            broker.state_path.write_text(
                json.dumps(
                    {
                        "state": "known-state",
                        "created_at": 0,
                        "redirect_uri": broker.redirect_uri(),
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(GoogleOAuthError, "expired"):
                broker.complete(code="fake-code", state="known-state")
            self.assertFalse(broker.state_path.exists())

    def test_id_token_rejects_non_rs256_without_network(self) -> None:
        token = ".".join(
            [
                base64.urlsafe_b64encode(json.dumps({"alg": "none", "kid": "x"}).encode()).decode().rstrip("="),
                base64.urlsafe_b64encode(json.dumps({"iss": "https://accounts.google.com"}).encode()).decode().rstrip("="),
                "",
            ]
        )
        with self.assertRaisesRegex(GoogleOAuthError, "unsupported signing algorithm"):
            GoogleOAuthBroker._verify_id_token(
                token,
                nonce="expected",
                client_id="client.apps.googleusercontent.com",
            )


if __name__ == "__main__":
    unittest.main()
