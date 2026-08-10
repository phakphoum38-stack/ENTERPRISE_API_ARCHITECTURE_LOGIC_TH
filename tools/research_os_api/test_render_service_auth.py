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
        self.original_secret = os.environ.get("RESEARCH_OS_IDENTITY_PROXY_SECRET")
        self.started: list[tuple[ThreadingHTTPServer, threading.Thread]] = []

    def tearDown(self) -> None:
        for server, thread in reversed(self.started):
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
        if self.original_secret is None:
            os.environ.pop("RESEARCH_OS_IDENTITY_PROXY_SECRET", None)
        else:
            os.environ["RESEARCH_OS_IDENTITY_PROXY_SECRET"] = self.original_secret

    def start_server(self, bind_host: str) -> str:
        server = ThreadingHTTPServer((bind_host, 0), CloudResearchOSHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.started.append((server, thread))
        return f"http://127.0.0.1:{server.server_port}"

    @staticmethod
    def request(base: str, headers=None):
        request = urllib.request.Request(
            base + "/health",
            headers=headers or {},
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def test_loopback_mode_remains_available_without_identity_headers(self) -> None:
        os.environ.pop("RESEARCH_OS_IDENTITY_PROXY_SECRET", None)
        base = self.start_server("127.0.0.1")
        status, payload = self.request(base)
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "ok")

    def test_exposed_mode_requires_valid_fresh_signed_identity(self) -> None:
        secret = "render-service-auth-test-secret-123456"
        os.environ["RESEARCH_OS_IDENTITY_PROXY_SECRET"] = secret
        base = self.start_server("0.0.0.0")

        status, payload = self.request(base)
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

        status, payload = self.request(base, headers)
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "ok")

        status, payload = self.request(base, headers)
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "service_identity_required")


if __name__ == "__main__":
    unittest.main()
