from __future__ import annotations

import json
import os
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

from render_server import CloudResearchOSHandler


class RenderServerCompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_provider = os.environ.get("RESEARCH_OS_PROVIDER")
        self.original_openai_key = os.environ.get("RESEARCH_OS_OPENAI_API_KEY")
        os.environ["RESEARCH_OS_PROVIDER"] = "mock"
        os.environ["RESEARCH_OS_OPENAI_API_KEY"] = "fixture-secret-value-should-never-leak"
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), CloudResearchOSHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        if self.original_provider is None:
            os.environ.pop("RESEARCH_OS_PROVIDER", None)
        else:
            os.environ["RESEARCH_OS_PROVIDER"] = self.original_provider
        if self.original_openai_key is None:
            os.environ.pop("RESEARCH_OS_OPENAI_API_KEY", None)
        else:
            os.environ["RESEARCH_OS_OPENAI_API_KEY"] = self.original_openai_key

    def request(self, path: str) -> dict[str, object]:
        with urllib.request.urlopen(self.base + path, timeout=5) as response:
            self.assertEqual(response.status, 200)
            return json.loads(response.read().decode("utf-8"))

    def test_master_contract_exposes_6x3_and_6x6_capacity(self) -> None:
        payload = self.request("/v2/master")
        master = payload["master"]
        self.assertEqual(master["contract"], "unified-master-orchestrator-v3")
        self.assertEqual(master["capacity"]["assistant_6x3_capacity"], 216)
        self.assertEqual(master["capacity"]["max_leaf_capacity"], 46656)

    def test_provider_status_is_secret_safe(self) -> None:
        payload = self.request("/v2/brain/providers")
        serialized = json.dumps(payload)
        self.assertTrue(payload["providers"]["safe"])
        self.assertNotIn("fixture-secret-value-should-never-leak", serialized)
        self.assertNotIn("Bearer ", serialized)


if __name__ == "__main__":
    unittest.main()
