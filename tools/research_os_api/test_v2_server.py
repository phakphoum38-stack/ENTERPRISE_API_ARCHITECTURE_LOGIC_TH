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
from unittest.mock import patch

import agent_server
from agent_orchestrator import AgentOrchestrator
from providers import ProviderError, ProviderResult
from v2_server import Provenance, V2ResearchOSHandler, WorkspaceKnowledgeEngine


class V2CompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original = agent_server.ORCHESTRATOR
        self.original_data_dir = os.environ.get("RESEARCH_OS_DATA_DIR")
        self.temp = tempfile.TemporaryDirectory()
        os.environ["RESEARCH_OS_DATA_DIR"] = self.temp.name
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
        if self.original_data_dir is None:
            os.environ.pop("RESEARCH_OS_DATA_DIR", None)
        else:
            os.environ["RESEARCH_OS_DATA_DIR"] = self.original_data_dir
        self.temp.cleanup()

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

    def create_run(self, index: int) -> str:
        status, created = self.request(
            "/v2/orchestrations",
            method="POST",
            body={
                "objective": f"V2 compatibility run {index}",
                "steps": [
                    {
                        "step_id": "research",
                        "objective": f"research compatibility evidence {index}",
                        "requested_agent": "research",
                    }
                ],
            },
        )
        self.assertEqual(status, 201)
        self.assertEqual(created["api_version"], "v2")
        return created["run"]["run_id"]

    def test_v1_and_v2_agent_catalog_share_registry(self) -> None:
        status_v1, v1 = self.request("/v1/agents")
        status_v2, v2 = self.request("/v2/agents")
        self.assertEqual((status_v1, status_v2), (200, 200))
        self.assertEqual(v2["api_version"], "v2")
        self.assertEqual(v1["count"], v2["count"])
        self.assertEqual(
            {item["agent_id"] for item in v1["agents"]},
            {item["agent_id"] for item in v2["agents"]},
        )

    def test_v2_orchestration_is_visible_through_v1(self) -> None:
        run_id = self.create_run(1)

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

    def test_v2_cursor_pagination_preserves_filters(self) -> None:
        ids = [self.create_run(index) for index in range(3)]
        status, first = self.request(
            "/v2/orchestrations?page_size=2&q=compatibility&agent=research"
        )
        self.assertEqual(status, 200)
        self.assertEqual(first["api_version"], "v2")
        self.assertEqual(len(first["items"]), 2)
        self.assertEqual(first["page"]["page_size"], 2)
        cursor = first["page"]["next_cursor"]
        self.assertIsInstance(cursor, str)

        status, second = self.request(
            f"/v2/orchestrations?page_size=2&q=compatibility&agent=research&cursor={cursor}"
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(second["items"]), 1)
        self.assertIsNone(second["page"]["next_cursor"])
        returned = {item["run_id"] for item in first["items"] + second["items"]}
        self.assertEqual(returned, set(ids))

    def test_v2_workspace_catalog_and_knowledge_search_use_existing_index(self) -> None:
        engine = WorkspaceKnowledgeEngine(self.temp.name)
        engine.create_workspace("Research", workspace_id="research")
        for index in range(2):
            engine.upsert_record(
                "research",
                kind="research_artifact",
                title=f"Evidence {index}",
                content=f"durable workspace evidence record {index}",
                provenance=Provenance(
                    source_type="research_artifact",
                    source_id=f"artifact-{index}",
                    evidence=[f"source-{index}"],
                ),
            )

        status, catalog = self.request("/v2/workspaces")
        self.assertEqual(status, 200)
        self.assertEqual(catalog["api_version"], "v2")
        self.assertEqual(catalog["count"], 1)
        self.assertEqual(catalog["workspaces"][0]["workspace_id"], "research")

        status, first = self.request(
            "/v2/workspaces/research/knowledge?q=evidence&page_size=1"
        )
        self.assertEqual(status, 200)
        self.assertEqual(first["workspace_id"], "research")
        self.assertEqual(len(first["items"]), 1)
        self.assertEqual(first["items"][0]["provenance"]["source_type"], "research_artifact")
        cursor = first["page"]["next_cursor"]
        self.assertIsInstance(cursor, str)

        status, second = self.request(
            f"/v2/workspaces/research/knowledge?q=evidence&page_size=1&cursor={cursor}"
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(second["items"]), 1)
        self.assertIsNone(second["page"]["next_cursor"])

        status, missing = self.request("/v2/workspaces/missing/knowledge?q=x")
        self.assertEqual(status, 404)
        self.assertEqual(missing["error"]["code"], "workspace_not_found")

    def test_v2_brain_skills_and_adaptive_capacity_are_additive(self) -> None:
        status, capacity = self.request("/v2/brain/capacity")
        self.assertEqual(status, 200)
        self.assertEqual(capacity["api_version"], "v2")
        self.assertEqual(capacity["capacity"]["branch_factor"], 6)
        self.assertEqual(capacity["capacity"]["elastic_tiers"], 6)
        self.assertEqual(capacity["capacity"]["max_leaf_capacity"], 6**6)
        self.assertFalse(capacity["capacity"]["all_workers_started_by_default"])

        status, skills = self.request("/v2/brain/skills")
        self.assertEqual(status, 200)
        self.assertEqual(skills["brain"]["skill_count"], 10)

        status, planned = self.request(
            "/v2/brain/plans",
            method="POST",
            body={
                "objective": "research evidence with agent tools",
                "complexity_level": 6,
                "requested_workers": 46656,
                "budget_workers": 12,
                "ready_workers": 8,
            },
        )
        self.assertEqual(status, 201)
        self.assertEqual(planned["plan"]["hierarchy"]["active_workers"], 8)
        self.assertTrue(planned["plan"]["hierarchy"]["backpressure_applied"])
        self.assertFalse(planned["plan"]["requires_external_api_key"])
        self.assertEqual(planned["plan"]["cognition"]["mode"], "compound_6x6")
        self.assertEqual(planned["plan"]["cognition"]["hypothesis_branches"], 8)

        status, invalid = self.request(
            "/v2/brain/plans",
            method="POST",
            body={"objective": "invalid", "complexity_level": 7},
        )
        self.assertEqual(status, 400)
        self.assertEqual(invalid["error"]["code"], "invalid_brain_plan")

    def test_v2_brain_discovers_existing_key_without_returning_secret(self) -> None:
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-existing-key"}):
            status, payload = self.request("/v2/brain/providers")
        self.assertEqual(status, 200)
        openai = payload["providers"]["openai-responses"]
        self.assertTrue(openai["configured"])
        self.assertEqual(openai["credential_source"], "OPENAI_API_KEY")
        self.assertFalse(openai["secret_exposed"])
        self.assertNotIn("test-existing-key", json.dumps(payload))

    def test_v2_brain_search_uses_compound_plan_and_returns_sources(self) -> None:
        class FakeSearchProvider:
            name = "openai-responses"

            def search(self, query, *, system="", model=None):
                self.query = query
                self.system = system
                return ProviderResult(
                    self.name,
                    model or "test-model",
                    "Verified answer",
                    {},
                    ({"url": "https://example.com", "title": "Evidence"},),
                )

        fake = FakeSearchProvider()
        with patch("v2_server.build_search_provider", return_value=fake):
            status, payload = self.request(
                "/v2/brain/search",
                method="POST",
                body={
                    "query": "ค้นข้อมูลล่าสุดพร้อมหลักฐาน",
                    "complexity_level": 6,
                    "budget_workers": 12,
                    "ready_workers": 8,
                },
            )
        self.assertEqual(status, 200)
        self.assertEqual(payload["result"]["text"], "Verified answer")
        self.assertEqual(payload["result"]["sources"][0]["title"], "Evidence")
        self.assertEqual(payload["brain_plan"]["cognition"]["mode"], "compound_6x6")
        self.assertEqual(payload["brain_plan"]["hierarchy"]["active_workers"], 8)
        self.assertIn("Cite sources", fake.system)

    def test_v2_brain_search_fails_closed_when_provider_is_unavailable(self) -> None:
        with patch(
            "v2_server.build_search_provider",
            side_effect=ProviderError("missing OpenAI API key"),
        ):
            status, payload = self.request(
                "/v2/brain/search",
                method="POST",
                body={"query": "current evidence"},
            )
        self.assertEqual(status, 503)
        self.assertEqual(payload["error"]["code"], "brain_provider_unavailable")

    def test_v2_errors_have_machine_readable_envelope(self) -> None:
        status, payload = self.request("/v2/orchestrations?page_size=101")
        self.assertEqual(status, 400)
        self.assertEqual(payload["api_version"], "v2")
        self.assertEqual(payload["error"]["code"], "invalid_pagination")
        self.assertEqual(payload["error"]["status"], 400)
        self.assertIn("page_size", payload["error"]["message"])

        status, missing = self.request("/v2/orchestrations/does-not-exist")
        self.assertEqual(status, 404)
        self.assertEqual(missing["error"]["code"], "orchestration_not_found")
        self.assertEqual(missing["error"]["status"], 404)


if __name__ == "__main__":
    unittest.main()
