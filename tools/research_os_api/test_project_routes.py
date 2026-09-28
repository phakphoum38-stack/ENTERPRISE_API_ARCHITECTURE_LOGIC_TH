from __future__ import annotations

import json
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

from server import ResearchOSHandler


class ProjectRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), ResearchOSHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def test_project_registry_snapshot_is_real_and_shared(self) -> None:
        with urllib.request.urlopen(self.base + "/v1/projects", timeout=5) as response:
            self.assertEqual(response.status, 200)
            payload = json.loads(response.read().decode("utf-8"))

        self.assertEqual(payload["source"], "ProjectRegistry")
        self.assertEqual(payload["configured_count"], 1)
        self.assertEqual(payload["supported_project_contexts"], 100)
        self.assertEqual(payload["scale_levels"], [10, 20, 50, 100])
        self.assertEqual(payload["release_authority"], "FINAL_GATE")
        self.assertEqual(
            payload["shared_planes"],
            {
                "capability_registry": "SHARED_CAPABILITY_REGISTRY",
                "queue": "SHARED_QUEUE",
                "evidence_ledger": "SHARED_EVIDENCE_LEDGER",
            },
        )
        self.assertEqual(payload["projects"][0]["project_id"], "project-001")
        self.assertEqual(
            payload["projects"][0]["evidence_namespace"],
            "PROJECT:project-001",
        )


if __name__ == "__main__":
    unittest.main()
