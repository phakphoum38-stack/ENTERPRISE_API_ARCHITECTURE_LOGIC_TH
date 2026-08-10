#!/usr/bin/env python3
from __future__ import annotations

import time
import unittest
import uuid

from developer_identity import IdentityAssertionVerifier
from v2_service_auth import (
    ServiceExposureAuthError,
    is_loopback_host,
    verify_service_request,
)


class ServiceExposureAuthTests(unittest.TestCase):
    def test_loopback_remains_local_first_without_shared_secret(self) -> None:
        self.assertTrue(is_loopback_host("127.0.0.1"))
        self.assertTrue(is_loopback_host("::1"))
        self.assertTrue(is_loopback_host("localhost"))
        self.assertIsNone(verify_service_request({}, bind_host="127.0.0.1"))

    def test_non_loopback_fails_closed_without_identity_configuration(self) -> None:
        with self.assertRaisesRegex(
            ServiceExposureAuthError,
            "requires signed identity configuration",
        ):
            verify_service_request({}, bind_host="0.0.0.0", secret="")

    def test_non_loopback_accepts_existing_signed_identity_contract(self) -> None:
        secret = "service-auth-test-secret-123456"
        principal = "research-os-app"
        issued_at = int(time.time())
        nonce = f"nonce-{uuid.uuid4().hex}"
        signer = IdentityAssertionVerifier(secret, max_age_seconds=120)
        headers = {
            "X-ResearchOS-Principal": principal,
            "X-ResearchOS-Identity-Timestamp": str(issued_at),
            "X-ResearchOS-Identity-Nonce": nonce,
            "X-ResearchOS-Identity-Signature": signer.signature_for(
                principal,
                issued_at,
                nonce,
            ),
        }

        identity = verify_service_request(
            headers,
            bind_host="0.0.0.0",
            secret=secret,
            max_age_seconds=120,
        )
        self.assertIsNotNone(identity)
        self.assertEqual(identity.principal, principal)

        with self.assertRaisesRegex(ServiceExposureAuthError, "replay detected"):
            verify_service_request(
                headers,
                bind_host="0.0.0.0",
                secret=secret,
                max_age_seconds=120,
            )


if __name__ == "__main__":
    unittest.main()
