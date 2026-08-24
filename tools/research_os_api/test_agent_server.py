from __future__ import annotations

import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import agent_server
from agent_orchestrator import AgentOrchestrator
from auth_session import issue_session


class AgentServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original = agent_server.ORCHESTRATOR
        self.original_secret = os.environ.get("RESEARCH_OS_SESSION_SECRET")
        os.environ["RESEARCH_OS_SESSION_SECRET"] = "test-only-agent-server-session-secret"
        self.session = issue_session({"sub": "agent-test-user", "email": "agent-test@example.test", "role": "user"})
        self.temp_dir = tempfile.TemporaryDirectory()
        agent_server.ORCHESTRATOR = AgentOrchestrator(
            storage_path=Path(self.temp_dir.name) / "agents" / "orchestrations.json",
        )
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), agent_server.AgentResearchOSHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        agent_server.ORCHESTRATOR = self.original
        if self.original_secret is None:
            os.environ.pop("RESEARCH_OS_SESSION_SECRET", None)
        else:
            os.environ["RESEARCH_OS_SESSION_SECRET"] = self.original_secret
        self.temp_dir.cleanup()

    def request(self, path: str, *, method: str = "GET", body=None, authenticated: bool = True):
        data = None if body is None else json.dumps(body).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if authenticated:
            headers["X-Research-OS-Session"] = self.session
        request = urllib.request.Request(
            self.base + path,
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def test_agent_discovery_and_readiness_routes(self) -> None:
        status, listed = self.request("/v1/agents")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(listed["count"], 6)
        ids = {agent["agent_id"] for agent in listed["agents"]}
        self.assertIn("developer", ids)
        self.assertIn("research", ids)

        status, readiness = self.request("/v1/agents/readiness")
        self.assertEqual(status, 200)
        self.assertTrue(readiness["ready"])
        self.assertEqual(readiness["ready_count"], readiness["agent_count"])

        status, discovered = self.request("/v1/agents/discover?capability=debug")
        self.assertEqual(status, 200)
        self.assertEqual(discovered["count"], 1)
        self.assertEqual(discovered["agents"][0]["agent_id"], "developer")
        self.assertTrue(discovered["filters"]["ready_only"])

    def test_create_get_list_and_execute(self) -> None:
        status, created = self.request(
            "/v1/agents/orchestrations",
            method="POST",
            body={
                "objective": "research and summarize repository state",
                "steps": [
                    {"step_id": "research", "objective": "research repository architecture", "requested_agent": "research"},
                    {"step_id": "github", "objective": "review github repository workflow", "requested_agent": "github", "depends_on": ["research"]},
                ],
            },
        )
        self.assertEqual(status, 201)
        run_id = created["run"]["run_id"]
        self.assertEqual(created["run"]["status"], "planned")
        self.assertEqual(created["run"]["events"][0]["event_type"], "run.created")

        status, listed = self.request("/v1/agents/orchestrations")
        self.assertEqual(status, 200)
        self.assertEqual(listed["count"], 1)
        self.assertEqual(listed["runs"][0]["run_id"], run_id)

        status, fetched = self.request(f"/v1/agents/orchestrations/{run_id}")
        self.assertEqual(status, 200)
        self.assertEqual(fetched["run"]["objective"], "research and summarize repository state")

        status, executed = self.request(f"/v1/agents/orchestrations/{run_id}/execute", method="POST", body={})
        self.assertEqual(status, 200)
        self.assertEqual(executed["run"]["status"], "completed")
        self.assertTrue(all(step["status"] == "completed" for step in executed["run"]["steps"]))
        self.assertTrue(all(step["attempt_count"] == 1 for step in executed["run"]["steps"]))

    def test_history_filters_and_timeline(self) -> None:
        status, research = self.request(
            "/v1/agents/orchestrations",
            method="POST",
            body={"objective": "research durable history", "steps": [{"step_id": "research", "objective": "inspect repository history", "requested_agent": "research"}]},
        )
        self.assertEqual(status, 201)
        research_id = research["run"]["run_id"]

        status, shift = self.request(
            "/v1/agents/orchestrations",
            method="POST",
            body={"objective": "sync shift calendar", "steps": [{"step_id": "shift", "objective": "calendar_sync shift roster", "requested_agent": "shift"}]},
        )
        self.assertEqual(status, 201)
        shift_id = shift["run"]["run_id"]

        status, executed = self.request(f"/v1/agents/orchestrations/{research_id}/execute", method="POST", body={})
        self.assertEqual(status, 200)
        self.assertEqual(executed["run"]["status"], "completed")

        status, filtered = self.request("/v1/agents/orchestrations?status=completed&agent=research&q=history&limit=10")
        self.assertEqual(status, 200)
        self.assertEqual(filtered["count"], 1)
        self.assertEqual(filtered["runs"][0]["run_id"], research_id)
        self.assertEqual(filtered["filters"]["status"], "completed")
        self.assertEqual(filtered["filters"]["agent"], "research")

        status, shift_filtered = self.request("/v1/agents/orchestrations?agent=shift")
        self.assertEqual(status, 200)
        self.assertEqual(shift_filtered["count"], 1)
        self.assertEqual(shift_filtered["runs"][0]["run_id"], shift_id)

        status, timeline = self.request(f"/v1/agents/orchestrations/{research_id}/timeline")
        self.assertEqual(status, 200)
        self.assertEqual(timeline["run_id"], research_id)
        self.assertGreaterEqual(timeline["count"], 4)
        event_types = [event["event_type"] for event in timeline["events"]]
        self.assertIn("run.created", event_types)
        self.assertIn("run.execution_started", event_types)
        self.assertIn("step.attempt_started", event_types)
        self.assertIn("step.completed", event_types)
        self.assertIn("run.status_changed", event_types)

        status, invalid = self.request("/v1/agents/orchestrations?limit=201")
        self.assertEqual(status, 400)
        self.assertEqual(invalid["error"], "bad_request")

    def test_confirmation_route_resumes_write_capable_plan(self) -> None:
        status, created = self.request(
            "/v1/agents/orchestrations",
            method="POST",
            body={"objective": "analyze and sync shift calendar", "steps": [{"step_id": "shift", "objective": "analyze shift roster and calendar_sync", "requested_agent": "shift"}]},
        )
        self.assertEqual(status, 201)
        run_id = created["run"]["run_id"]

        status, executed = self.request(f"/v1/agents/orchestrations/{run_id}/execute", method="POST", body={})
        self.assertEqual(status, 200)
        self.assertEqual(executed["run"]["status"], "awaiting_confirmation")

        status, confirmed = self.request(f"/v1/agents/orchestrations/{run_id}/confirm", method="POST", body={})
        self.assertEqual(status, 200)
        self.assertEqual(confirmed["run"]["status"], "completed")

    def test_cancel_and_retry_routes(self) -> None:
        status, created = self.request(
            "/v1/agents/orchestrations",
            method="POST",
            body={"objective": "cancel this run", "steps": [{"step_id": "research", "objective": "wait for cancellation", "requested_agent": "research", "max_attempts": 2}]},
        )
        self.assertEqual(status, 201)
        run_id = created["run"]["run_id"]
        self.assertEqual(created["run"]["steps"][0]["max_attempts"], 2)

        status, retry = self.request(f"/v1/agents/orchestrations/{run_id}/retry", method="POST", body={"step_id": "research"})
        self.assertEqual(status, 400)
        self.assertIn("no retryable failed steps", retry["detail"])

        status, cancelled = self.request(f"/v1/agents/orchestrations/{run_id}/cancel", method="POST", body={})
        self.assertEqual(status, 200)
        self.assertEqual(cancelled["run"]["status"], "cancelled")
        self.assertEqual(cancelled["run"]["steps"][0]["status"], "cancelled")

        status, blocked = self.request(f"/v1/agents/orchestrations/{run_id}/execute", method="POST", body={})
        self.assertEqual(status, 400)
        self.assertIn("cancelled", blocked["detail"])

    def test_rejects_invalid_contract_and_unknown_run(self) -> None:
        status, payload = self.request("/v1/agents/orchestrations", method="POST", body={"objective": "bad", "steps": "not-an-array"})
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "bad_request")

        status, payload = self.request(
            "/v1/agents/orchestrations",
            method="POST",
            body={"objective": "bad retry limit", "steps": [{"step_id": "x", "objective": "x", "max_attempts": 6}]},
        )
        self.assertEqual(status, 400)
        self.assertIn("max_attempts", payload["detail"])

        status, payload = self.request("/v1/agents/orchestrations/missing")
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"], "orchestration_not_found")

        status, payload = self.request("/v1/agents/orchestrations/missing/timeline")
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"], "orchestration_not_found")

    def test_protected_routes_fail_closed_without_session(self) -> None:
        status, payload = self.request("/v1/agents", authenticated=False)
        self.assertEqual(status, 401)
        self.assertIn("error", payload)


if __name__ == "__main__":
    unittest.main()
