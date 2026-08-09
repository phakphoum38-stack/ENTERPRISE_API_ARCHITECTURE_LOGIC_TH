from __future__ import annotations

import http.client
import json
import os
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer

from developer_server import DeveloperPlatformHandler


class DeveloperTrialPageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.old_data = os.environ.get("RESEARCH_OS_DATA_DIR")
        self.old_secret = os.environ.get("RESEARCH_OS_IDENTITY_PROXY_SECRET")
        os.environ["RESEARCH_OS_DATA_DIR"] = self.temp.name
        os.environ["RESEARCH_OS_IDENTITY_PROXY_SECRET"] = "test-gateway-secret"
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), DeveloperPlatformHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        if self.old_data is None:
            os.environ.pop("RESEARCH_OS_DATA_DIR", None)
        else:
            os.environ["RESEARCH_OS_DATA_DIR"] = self.old_data
        if self.old_secret is None:
            os.environ.pop("RESEARCH_OS_IDENTITY_PROXY_SECRET", None)
        else:
            os.environ["RESEARCH_OS_IDENTITY_PROXY_SECRET"] = self.old_secret
        self.temp.cleanup()

    def raw_request(self, method: str, path: str, body: dict | None = None):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_address[1], timeout=5)
        payload = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Content-Type": "application/json"} if payload is not None else {}
        conn.request(method, path, body=payload, headers=headers)
        response = conn.getresponse()
        raw = response.read()
        result = response.status, dict(response.getheaders()), raw
        conn.close()
        return result

    def test_trial_page_is_available_without_registration(self) -> None:
        status, headers, raw = self.raw_request("GET", "/trial")
        self.assertEqual(status, 200)
        self.assertIn("text/html", headers.get("Content-Type", ""))
        html = raw.decode("utf-8")
        self.assertIn("Developer Trial", html)
        self.assertIn("ไม่ต้องลงทะเบียน", html)
        self.assertIn("/v2/developer/trial/resources", html)
        self.assertNotIn("http://127.0.0.1:8790", html)
        self.assertIn("frame-ancestors 'none'", headers.get("Content-Security-Policy", ""))

    def test_trial_api_works_without_identity_but_real_grants_do_not(self) -> None:
        status, _, raw = self.raw_request("GET", "/v2/developer/trial/resources")
        self.assertEqual(status, 200)
        payload = json.loads(raw.decode("utf-8"))
        self.assertEqual(payload["mode"], "trial")
        self.assertGreater(payload["count"], 0)

        status, _, raw = self.raw_request("GET", "/v2/developer/grants")
        self.assertEqual(status, 401)
        payload = json.loads(raw.decode("utf-8"))
        self.assertEqual(payload["error"]["code"], "identity_required")

    def test_trial_write_simulation_is_denied(self) -> None:
        status, _, raw = self.raw_request(
            "POST",
            "/v2/developer/trial/authorize",
            {"resource_id": "demo-api-client", "scope": "write"},
        )
        self.assertEqual(status, 403)
        payload = json.loads(raw.decode("utf-8"))
        self.assertEqual(payload["error"]["code"], "trial_restricted")


if __name__ == "__main__":
    unittest.main()
