from __future__ import annotations

import unittest

from developer_identity import IdentityAssertionError, IdentityAssertionVerifier


class IdentityAssertionVerifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.verifier = IdentityAssertionVerifier("production-test-secret-32-bytes", max_age_seconds=120)

    def headers(self, principal: str = "dev:alice", issued_at: int = 1000, nonce: str = "nonce-abcdefghijklmnop") -> dict[str, str]:
        return {
            "X-ResearchOS-Principal": principal,
            "X-ResearchOS-Identity-Timestamp": str(issued_at),
            "X-ResearchOS-Identity-Nonce": nonce,
            "X-ResearchOS-Identity-Signature": self.verifier.signature_for(principal, issued_at, nonce),
        }

    def test_valid_signed_assertion_is_accepted_once(self) -> None:
        identity = self.verifier.verify(self.headers(), now=1050)
        self.assertEqual(identity.principal, "dev:alice")
        self.assertEqual(identity.mode, "signed_assertion")

    def test_tampered_principal_is_rejected(self) -> None:
        headers = self.headers()
        headers["X-ResearchOS-Principal"] = "dev:mallory"
        with self.assertRaisesRegex(IdentityAssertionError, "signature"):
            self.verifier.verify(headers, now=1050)

    def test_expired_assertion_is_rejected(self) -> None:
        with self.assertRaisesRegex(IdentityAssertionError, "expired"):
            self.verifier.verify(self.headers(), now=1201)

    def test_future_assertion_outside_clock_skew_is_rejected(self) -> None:
        with self.assertRaisesRegex(IdentityAssertionError, "future"):
            self.verifier.verify(self.headers(issued_at=1100), now=1000)

    def test_nonce_replay_is_rejected(self) -> None:
        headers = self.headers()
        self.verifier.verify(headers, now=1050)
        with self.assertRaisesRegex(IdentityAssertionError, "replay"):
            self.verifier.verify(headers, now=1051)

    def test_short_gateway_secret_is_rejected(self) -> None:
        with self.assertRaisesRegex(IdentityAssertionError, "too short"):
            IdentityAssertionVerifier("short")


if __name__ == "__main__":
    unittest.main()
