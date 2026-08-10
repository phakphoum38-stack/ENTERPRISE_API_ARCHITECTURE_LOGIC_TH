#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import threading
import time
import unittest
import urllib.error
import urllib.request
import uuid
from http.server import ThreadingHTTPServer

from developer_identity import IdentityAssertionVerifier
from render_server import CloudResearchOSHandler


class RenderServiceAuthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_host = os.environ.get("RESEARCH_OS_API_HOST")
        self.original_secret = os.environ.get("RESEARCH_OS_IDENTITY_PROXY_SECRET")
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), CloudResearchOSHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        if self.original_host is None:
            os.environ.pop("RESEARCH_OS_API_HOST", None)
        else:
            os.environ["RESEARCH_OS_API_HOST"] = self.original_host
        if self.original_secret is None:
            os.environ.pop("RESEARCH_OS_IDENTITY_PROXY_SECRET", None)
        else:
            os.environ["RESEARCH_OS_IDENTITY_PROXY_SECRET"] = self.original_secret

    def request(self, headers=None):
        request = urllib.request.Request(
            self.base + "/health",
            headers=headers or {},
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def test_loopback_mode_remains_available_without_identity_headers(self) -> None:
        os.environ["RESEARCH_OS_API_HOST"] = "127.0.0.1"
        os.environ.pop("RESEARCH_OS_IDENTITY_PROXY_SECRET", None)
        status, payload = self.request()
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "ok")

    def test_exposed_mode_requires_valid_fresh_signed_identity(self) -> None:
        secret = "render-service-auth-test-secret-123456"
        os.environ["RESEARCH_OS_API_HOST"] = "0.0.0.0"
        os.environ["RESEARCH_OS_IDENTITY_PROXY_SECRET"] = secret

        status, payload = self.request()
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "service_identity_required")

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

        status, payload = self.request(headers)
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "ok")

        status, payload = self.request(headers)
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "service_identity_required")


if __name__ == "__main__":
    unittest.main()
