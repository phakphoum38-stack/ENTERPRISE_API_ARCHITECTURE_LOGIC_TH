#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from v2_server import V2ResearchOSHandler
from v2_system_introspection import SYSTEM_INTROSPECTION_CONTRACT


class V2IntelligenceServerPhase7Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_data_dir = os.environ.get("RESEARCH_OS_DATA_DIR")
        self.temp = tempfile.TemporaryDirectory()
        os.environ["RESEARCH_OS_DATA_DIR"] = self.temp.name
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), V2ResearchOSHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
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

    def test_manifest_and_health_are_v2_read_only_contracts(self) -> None:
        status, manifest = self.request("/v2/intelligence")
        self.assertEqual(200, status)
        self.assertEqual("v2", manifest["api_version"])
        self.assertEqual(SYSTEM_INTROSPECTION_CONTRACT, manifest["contract"])
        self.assertTrue(manifest["read_only"])
        self.assertFalse(manifest["execution_authority"])

        status, health = self.request("/v2/intelligence/health")
        self.assertEqual(200, status)
        self.assertTrue(health["ready"])
        self.assertFalse(health["safety"]["introspection_grants_permissions"])

    def test_capability_agent_skill_tool_and_permission_catalogs_are_queryable(self) -> None:
        status, capabilities = self.request("/v2/intelligence/capabilities")
        self.assertEqual(200, status)
        names = {item["capability"] for item in capabilities["capabilities"]}
        self.assertIn("skill_registry", names)

        status, agents = self.request(
            "/v2/intelligence/agents?scope=brain&capability=security_review"
        )
        self.assertEqual(200, status)
        self.assertEqual(
            ["v2_brain_reviewer"],
            [item["agent_id"] for item in agents["brain_team"]],
        )

        status, skills = self.request("/v2/intelligence/skills?ready_only=true")
        self.assertEqual(200, status)
        self.assertGreater(skills["count"], 0)

        status, tools = self.request("/v2/intelligence/tools?ready_only=true")
        self.assertEqual(200, status)
        self.assertGreater(tools["count"], 0)
        self.assertTrue(all(item["adapter_ready"] for item in tools["tools"]))

        status, permissions = self.request("/v2/intelligence/permissions")
        self.assertEqual(200, status)
        self.assertEqual("descriptive_only", permissions["authority"])
        self.assertTrue(
            all(not item["granted_by_introspection"] for item in permissions["permissions"])
        )

    def test_architecture_and_project_state_do_not_expose_private_storage_paths(self) -> None:
        status, architecture = self.request("/v2/intelligence/architecture")
        self.assertEqual(200, status)
        node_ids = {item["id"] for item in architecture["nodes"]}
        self.assertIn("execution_controller", node_ids)
        self.assertIn("ai_gateway", node_ids)

        private_path = self.temp.name
        status, state = self.request("/v2/intelligence/project-state")
        self.assertEqual(200, status)
        self.assertTrue(state["storage"]["data_dir_configured"])
        self.assertFalse(state["storage"]["data_dir_exposed"])
        self.assertNotIn(private_path, repr(state))
        self.assertFalse(state["authority"]["production_state_authoritative"])

    def test_plan_endpoint_is_read_only_and_secret_safe(self) -> None:
        secret = "sk-phase7httpsecret123456789"
        status, payload = self.request(
            "/v2/intelligence/plan",
            method="POST",
            body={
                "objective": f"analyze API architecture using {secret}",
                "session_id": "phase7-http",
                "context": {"workspace": "Research OS"},
            },
        )
        self.assertEqual(200, status)
        self.assertEqual("v2", payload["api_version"])
        self.assertTrue(payload["read_only"])
        self.assertFalse(payload["execution_performed"])
        self.assertIsInstance(payload["result"]["plan"], dict)
        self.assertNotIn(secret, repr(payload))
        self.assertIn("[REDACTED]", repr(payload))

    def test_invalid_scope_and_non_plan_post_fail_with_v2_error_envelope(self) -> None:
        status, invalid = self.request("/v2/intelligence/agents?scope=unknown")
        self.assertEqual(400, status)
        self.assertEqual("invalid_intelligence_query", invalid["error"]["code"])

        status, missing = self.request(
            "/v2/intelligence/tools",
            method="POST",
            body={},
        )
        self.assertEqual(404, status)
        self.assertEqual("intelligence_route_not_found", missing["error"]["code"])

    def test_plan_rejects_non_object_context(self) -> None:
        status, payload = self.request(
            "/v2/intelligence/plan",
            method="POST",
            body={"objective": "review architecture", "context": ["not", "an", "object"]},
        )
        self.assertEqual(400, status)
        self.assertEqual("invalid_intelligence_plan", payload["error"]["code"])


if __name__ == "__main__":
    unittest.main()
