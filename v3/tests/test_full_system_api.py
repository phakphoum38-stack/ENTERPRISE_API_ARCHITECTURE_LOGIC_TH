import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from research_os_v3 import DataLayout, V3LocalService


class FullSystemApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.service = V3LocalService(
            host="127.0.0.1",
            port=0,
            data_layout=DataLayout(Path(self.temporary.name)),
        )
        self.server = self.service.build_server()
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base = f"http://{host}:{port}"
        self.headers = {
            "X-Research-OS-User": "api-test-user",
            "X-Research-OS-Profile": "default",
            "Accept": "application/json",
        }

    def tearDown(self) -> None:
        self.service.shutdown()
        self.thread.join(timeout=2)
        self.temporary.cleanup()

    def get(self, path: str) -> tuple[int, dict[str, object]]:
        request = urllib.request.Request(self.base + path, headers=self.headers)
        with urllib.request.urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def post(
        self,
        path: str,
        payload: dict[str, object],
        *,
        approved: bool = False,
    ) -> tuple[int, dict[str, object]]:
        headers = dict(self.headers)
        headers["Content-Type"] = "application/json"
        if approved:
            headers["X-Research-OS-Approval"] = "granted"
        request = urllib.request.Request(
            self.base + path,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_capability_catalogs_and_10x10_health(self) -> None:
        status, health = self.get("/health")
        self.assertEqual(status, 200)
        self.assertEqual(health["maximum_scale"], "10^10")
        self.assertEqual(health["maximum_logical_capacity"], 10_000_000_000)
        self.assertEqual(health["capacity_policy"], "lazy-bounded-execution")

        catalogs = {}
        for path, key in (
            ("/v3/skills", "skills"),
            ("/v3/tools", "tools"),
            ("/v3/agents", "agents"),
            ("/v3/providers", "providers"),
        ):
            status, payload = self.get(path)
            self.assertEqual(status, 200)
            self.assertTrue(payload[key])
            catalogs[path] = payload

        skills = catalogs["/v3/skills"]
        self.assertGreaterEqual(skills["count"], 40)
        self.assertEqual(skills["single_authority"], "unified-master-orchestrator-v3-full")
        self.assertIn("owner-friend", skills["origins"])
        self.assertIn("legacy", skills["origins"])
        by_name = {item["name"]: item for item in skills["skills"]}
        names = set(by_name)
        self.assertTrue({"analysis", "coding", "research-curation", "v3-bridge"} <= names)
        self.assertTrue(by_name["chat-runtime"]["native_v3"])
        self.assertEqual(by_name["chat-runtime"]["runtime_mode"], "native")
        self.assertFalse(by_name["coding"]["native_v3"])
        self.assertEqual(by_name["coding"]["runtime_mode"], "context-adapter")

    def test_master_and_factory_plan_select_10x10_without_spawning_it(self) -> None:
        status, master = self.get("/v3/master?tasks=46657")
        self.assertEqual(status, 200)
        self.assertEqual(master["scale"], "10^10")
        self.assertEqual(master["maximum_leaf_capacity"], 10_000_000_000)
        self.assertEqual(master["system_maximum_scale"], "10^10")
        self.assertEqual(master["system_maximum_logical_capacity"], 10_000_000_000)
        self.assertNotIn("active_workers", master)

        status, plan = self.get("/v3/factory/plan?tasks=46657")
        self.assertEqual(status, 200)
        self.assertEqual(plan["scale"], "10^10")
        self.assertEqual(plan["maximum_leaf_capacity"], 10_000_000_000)
        self.assertEqual(
            plan["stage_order"],
            ["master", "factory", "team", "tests", "release"],
        )

    def test_memory_chat_agent_and_readonly_tool_flow(self) -> None:
        status, created = self.post(
            "/v3/memory",
            {
                "text": "Research OS full system uses ten to the tenth logical capacity",
                "tags": ["10x10"],
            },
        )
        self.assertEqual(status, 201)
        self.assertIn("memory", created)

        query = urllib.parse.quote("logical capacity")
        status, memory = self.get(f"/v3/memory?q={query}")
        self.assertEqual(status, 200)
        self.assertEqual(len(memory["memory"]), 1)

        status, chat = self.post("/v3/chat", {"prompt": "logical capacity"})
        self.assertEqual(status, 200)
        self.assertEqual(chat["provider"], "mock")
        self.assertTrue(chat["memory_hits"])

        status, agent = self.post(
            "/v3/agents/run",
            {"name": "architect", "prompt": "review the scaling model"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(agent["agent"], "architect")
        self.assertEqual(agent["provider"], "mock")

        status, tool = self.post(
            "/v3/tools/execute",
            {"name": "echo", "arguments": {"text": "tool-ok"}},
        )
        self.assertEqual(status, 200)
        self.assertEqual(tool["result"]["text"], "tool-ok")

    def test_write_tool_fails_closed_without_approval_and_succeeds_with_approval(self) -> None:
        payload = {
            "name": "artifact-note",
            "arguments": {"title": "approved-note", "text": "evidence"},
        }
        request = urllib.request.Request(
            self.base + "/v3/tools/execute",
            data=json.dumps(payload).encode("utf-8"),
            headers={**self.headers, "Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(urllib.error.HTTPError) as captured:
            urllib.request.urlopen(request, timeout=3)
        self.assertEqual(captured.exception.code, 403)

        status, result = self.post("/v3/tools/execute", payload, approved=True)
        self.assertEqual(status, 200)
        artifact_name = result["result"]["artifact"]
        self.assertTrue(artifact_name.endswith(".txt"))
        artifact_path = (
            Path(self.temporary.name)
            / "users"
            / "api-test-user"
            / "profiles"
            / "default"
            / "artifacts"
            / artifact_name
        )
        self.assertEqual(artifact_path.read_text(encoding="utf-8"), "evidence")


if __name__ == "__main__":
    unittest.main()
