from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import agent_server
from agent_orchestrator import AgentOrchestrator
from v2_server import V2ResearchOSHandler


class V2CompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original = agent_server.ORCHESTRATOR
        self.temp = tempfile.TemporaryDirectory()
        agent_server.ORCHESTRATOR = AgentOrchestrator(
            storage_path=Path(self.temp.name) / "agents" / "orchestrations.json"
        )
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), V2ResearchOSHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        agent_server.ORCHESTRATOR = self.original
        self.temp.cleanup()

    def request(self, path: str, *, method: str = "GET", body=None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            self.base + path,
            data=data,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_v1_and_v2_agent_catalog_share_registry(self) -> None:
        status_v1, v1 = self.request("/v1/agents")
        status_v2, v2 = self.request("/v2/agents")
        self.assertEqual((status_v1, status_v2), (200, 200))
        self.assertEqual(v1["count"], v2["count"])
        self.assertEqual(
            {item["agent_id"] for item in v1["agents"]},
            {item["agent_id"] for item in v2["agents"]},
        )

    def test_v2_orchestration_is_visible_through_v1(self) -> None:
        status, created = self.request(
            "/v2/orchestrations",
            method="POST",
            body={
                "objective": "V2 compatibility run",
                "steps": [
                    {
                        "step_id": "research",
                        "objective": "research compatibility evidence",
                        "requested_agent": "research",
                    }
                ],
            },
        )
        self.assertEqual(status, 201)
        run_id = created["run"]["run_id"]

        status_v1, v1 = self.request(f"/v1/agents/orchestrations/{run_id}")
        status_v2, v2 = self.request(f"/v2/orchestrations/{run_id}")
        self.assertEqual((status_v1, status_v2), (200, 200))
        self.assertEqual(v1["run"]["run_id"], run_id)
        self.assertEqual(v2["run"], v1["run"])

        execute_status, executed = self.request(
            f"/v2/orchestrations/{run_id}/execute",
            method="POST",
            body={},
        )
        self.assertEqual(execute_status, 200)
        self.assertEqual(executed["run"]["status"], "completed")

        _, history = self.request("/v1/agents/orchestrations?status=completed&limit=10")
        self.assertEqual(history["count"], 1)
        self.assertEqual(history["runs"][0]["run_id"], run_id)


if __name__ == "__main__":
    unittest.main()
