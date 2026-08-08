from __future__ import annotations

import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import agent_server
from agent_orchestrator import AgentOrchestrator


class AgentServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original = agent_server.ORCHESTRATOR
        agent_server.ORCHESTRATOR = AgentOrchestrator()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), agent_server.AgentResearchOSHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        agent_server.ORCHESTRATOR = self.original

    def request(self, path: str, *, method: str = "GET", body=None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            self.base + path,
            data=data,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def test_create_get_list_and_execute(self) -> None:
        status, created = self.request(
            "/v1/agents/orchestrations",
            method="POST",
            body={
                "objective": "research and summarize repository state",
                "steps": [
                    {
                        "step_id": "research",
                        "objective": "research repository architecture",
                        "requested_agent": "research",
                    },
                    {
                        "step_id": "github",
                        "objective": "review github repository workflow",
                        "requested_agent": "github",
                        "depends_on": ["research"],
                    },
                ],
            },
        )
        self.assertEqual(status, 201)
        run_id = created["run"]["run_id"]
        self.assertEqual(created["run"]["status"], "planned")

        status, listed = self.request("/v1/agents/orchestrations")
        self.assertEqual(status, 200)
        self.assertEqual(listed["count"], 1)
        self.assertEqual(listed["runs"][0]["run_id"], run_id)

        status, fetched = self.request(f"/v1/agents/orchestrations/{run_id}")
        self.assertEqual(status, 200)
        self.assertEqual(fetched["run"]["objective"], "research and summarize repository state")

        status, executed = self.request(
            f"/v1/agents/orchestrations/{run_id}/execute",
            method="POST",
            body={},
        )
        self.assertEqual(status, 200)
        self.assertEqual(executed["run"]["status"], "completed")
        self.assertTrue(all(step["status"] == "completed" for step in executed["run"]["steps"]))

    def test_confirmation_route_resumes_write_capable_plan(self) -> None:
        status, created = self.request(
            "/v1/agents/orchestrations",
            method="POST",
            body={
                "objective": "analyze and sync shift calendar",
                "steps": [
                    {
                        "step_id": "shift",
                        "objective": "analyze shift roster and calendar_sync",
                        "requested_agent": "shift",
                    }
                ],
            },
        )
        self.assertEqual(status, 201)
        run_id = created["run"]["run_id"]

        status, executed = self.request(
            f"/v1/agents/orchestrations/{run_id}/execute",
            method="POST",
            body={},
        )
        self.assertEqual(status, 200)
        self.assertEqual(executed["run"]["status"], "awaiting_confirmation")

        status, confirmed = self.request(
            f"/v1/agents/orchestrations/{run_id}/confirm",
            method="POST",
            body={},
        )
        self.assertEqual(status, 200)
        self.assertEqual(confirmed["run"]["status"], "completed")

    def test_rejects_invalid_contract_and_unknown_run(self) -> None:
        status, payload = self.request(
            "/v1/agents/orchestrations",
            method="POST",
            body={"objective": "bad", "steps": "not-an-array"},
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "bad_request")

        status, payload = self.request("/v1/agents/orchestrations/missing")
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"], "orchestration_not_found")


if __name__ == "__main__":
    unittest.main()
