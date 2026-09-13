import json
import os
import tempfile
import threading
import unittest
import urllib.parse
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import server
from auth_session import issue_session


class ResearchOSAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["RESEARCH_OS_SESSION_SECRET"] = "test-only-research-os-api-secret"
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.ResearchOSHandler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=2)

    def request(self, method: str, path: str, payload=None, headers=None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=data,
            headers=request_headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def issue_session(self, user_id: str = "copilot-user") -> str:
        return issue_session(
            {"sub": user_id, "email": f"{user_id}@example.test", "role": "user"}
        )

    def test_health(self):
        status, payload = self.request("GET", "/health")
        self.assertEqual(200, status)
        self.assertEqual("ok", payload["status"])
        self.assertTrue(payload["memory"])

    @patch.dict(
        os.environ,
        {"RESEARCH_OS_AI_ROUTE": "direct-provider"},
        clear=False,
    )
    def test_mock_provider_generation(self):
        status, payload = self.request("POST", "/v1/ai/generate", {
            "provider": "mock",
            "prompt": "วิเคราะห์แนวคิดนี้",
        })
        self.assertEqual(200, status)
        self.assertEqual("mock", payload["provider"])
        self.assertIn("วิเคราะห์", payload["text"])

    @patch("server._friend_chat")
    def test_generate_routes_through_friend_by_default(self, friend_chat):
        friend_chat.return_value = {
            "provider": "owner-mock",
            "text": "friend-ok",
            "decision": {
                "scale": "10^10",
                "capacity": 10_000_000_000,
            },
            "factory": {
                "available": True,
                "scale": "10^10",
                "capacity": 10_000_000_000,
            },
            "helpers": {
                "bounded": True,
                "active_workers": 128,
                "logical_capacity": 10_000_000_000,
            },
            "metadata": {
                "capabilities": ["v3-unified-master"],
            },
        }

        with patch.dict(
            os.environ,
            {"RESEARCH_OS_AI_ROUTE": "friend"},
            clear=False,
        ):
            status, payload = self.request(
                "POST",
                "/v1/ai/generate",
                {
                    "prompt": "mega project",
                    "session_id": "api-friend-test",
                    "complexity": 9,
                    "risk": 7,
                    "parallelism": 128,
                    "helper_budget": 1_000_000,
                },
            )

        self.assertEqual(200, status)
        self.assertEqual("friend", payload["route"])
        self.assertEqual("friend-ok", payload["text"])
        self.assertEqual("10^10", payload["decision"]["scale"])
        self.assertEqual("10^10", payload["factory"]["scale"])
        self.assertTrue(payload["helpers"]["bounded"])

    def test_memory_search(self):
        query = urllib.parse.quote("conversation knowledge")
        status, payload = self.request("GET", f"/v1/memory/search?q={query}&limit=3")
        self.assertEqual(200, status)
        self.assertGreaterEqual(payload["count"], 1)
        self.assertIn("artifact_id", payload["hits"][0])
        self.assertIn("score", payload["hits"][0])

    @patch.dict(
        os.environ,
        {"RESEARCH_OS_AI_ROUTE": "direct-provider"},
        clear=False,
    )
    def test_answer_with_memory_uses_mock_provider(self):
        status, payload = self.request("POST", "/v1/ai/answer-with-memory", {
            "provider": "mock",
            "question": "conversation knowledge",
            "session_id": "memory-test",
        })
        self.assertEqual(200, status)
        self.assertEqual("mock", payload["provider"])
        self.assertEqual("memory-test", payload["session_id"])
        self.assertGreaterEqual(payload["memory_count"], 1)
        self.assertTrue(payload["text"])

    def test_conversation_analysis_is_preview_only(self):
        status, payload = self.request("POST", "/v1/conversations/analyze", {
            "title": "API integration",
            "conversation": [
                {"role": "user", "content": "Research OS ควรมี API กลางและไม่ควรผูกกับผู้ให้บริการ AI รายเดียว"},
                {"role": "assistant", "content": "ควรใช้ Provider Interface และ Adapter เพื่อเปลี่ยนโมเดลได้"},
            ],
            "tags": ["api", "provider"],
        })
        self.assertEqual(200, status)
        self.assertFalse(payload["persisted"])
        self.assertIn("artifact_id", payload["artifact"])

    def test_memory_commit_requires_explicit_confirmation_and_sync_key(self):
        original_dir = server.ARTIFACT_DIR
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {"RESEARCH_OS_SYNC_KEY": "test-sync-key"},
            clear=False,
        ):
            server.ARTIFACT_DIR = Path(tmp)
            try:
                status, payload = self.request(
                    "POST",
                    "/v1/memory/commit",
                    {
                        "confirm": True,
                        "title": "Memory integration",
                        "conversation": [
                            {
                                "role": "user",
                                "content": "Research OS ต้องเก็บความรู้จาก Session แบบมีการยืนยันก่อนบันทึก",
                            },
                            {
                                "role": "assistant",
                                "content": "สรุปว่าควรใช้ explicit commit และค้นคืนผ่าน Memory Search",
                            },
                        ],
                        "tags": ["memory", "session"],
                        "min_quality": 20,
                    },
                    headers={"X-Research-OS-Sync-Key": "test-sync-key"},
                )
                self.assertEqual(200, status)
                self.assertTrue(payload["persisted"])
                self.assertEqual("runtime-ephemeral", payload["durability"])
                artifact_id = payload["artifact"]["artifact_id"]
                self.assertTrue(any(Path(tmp).glob(f"{artifact_id}*.md")))

                query = urllib.parse.quote("explicit commit")
                status, memory = self.request("GET", f"/v1/memory/search?q={query}")
                self.assertEqual(200, status)
                self.assertGreaterEqual(memory["count"], 1)
            finally:
                server.ARTIFACT_DIR = original_dir

    def test_provider_list(self):
        status, payload = self.request("GET", "/v1/providers")
        self.assertEqual(200, status)
        self.assertIn("mock", payload["providers"])
        self.assertIn("anthropic", payload["providers"])

    def test_copilot_context_requires_session(self):
        status, payload = self.request("GET", "/v1/copilot/context")
        self.assertEqual(400, status)
        self.assertEqual("bad_request", payload["error"])

    @patch("server.copilot_service._git_branch", return_value="feature/copilot")
    def test_copilot_context_returns_repo_scope_and_memory(self, _branch):
        status, payload = self.request(
            "GET",
            "/v1/copilot/context?query=conversation&path=README.md",
            headers={"X-Research-OS-Session": self.issue_session("alice")},
        )
        self.assertEqual(200, status)
        self.assertEqual(
            "phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH",
            payload["repository"],
        )
        self.assertEqual("feature/copilot", payload["branch"])
        self.assertEqual("user-alice", payload["scope"]["profile_id"])
        self.assertEqual("README.md", payload["files"][0]["path"])
        self.assertGreaterEqual(payload["memory_count"], 1)

    def test_copilot_context_rejects_out_of_contract_memory_limit(self):
        status, payload = self.request(
            "GET",
            "/v1/copilot/context?memory_limit=51",
            headers={"X-Research-OS-Session": self.issue_session("erin")},
        )
        self.assertEqual(400, status)
        self.assertIn("memory_limit must be between 1 and 50", payload["detail"])

    @patch("server.copilot_service.CopilotChatClient")
    def test_copilot_chat_routes_through_service_and_audits(self, client_cls):
        client_cls.return_value.chat.return_value = {
            "reply": "Copilot enterprise response",
            "model": "copilot-enterprise",
            "raw": {"reply": "Copilot enterprise response"},
        }
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {"RESEARCH_OS_COPILOT_AUDIT_DIR": tmp},
            clear=False,
        ):
            status, payload = self.request(
                "POST",
                "/v1/copilot/chat",
                {"message": "ช่วยสรุป architecture นี้"},
                headers={"X-Research-OS-Session": self.issue_session("bob")},
            )
            self.assertTrue(Path(tmp, "audit.jsonl").exists())
        self.assertEqual(200, status)
        self.assertEqual("copilot-chat", payload["provider"])
        self.assertEqual("Copilot enterprise response", payload["reply"])
        self.assertEqual("user-bob", payload["context"]["scope"]["profile_id"])
        self.assertTrue(payload["audit"]["written"])

    def test_copilot_chat_rejects_scope_override(self):
        status, payload = self.request(
            "POST",
            "/v1/copilot/chat",
            {"message": "hello", "user_id": "mallory"},
            headers={"X-Research-OS-Session": self.issue_session("carol")},
        )
        self.assertEqual(400, status)
        self.assertIn("cannot be overridden", payload["detail"])

    def test_copilot_chat_rejects_scope_override_even_with_falsey_values(self):
        status, payload = self.request(
            "POST",
            "/v1/copilot/chat",
            {"message": "hello", "role": False},
            headers={"X-Research-OS-Session": self.issue_session("grace")},
        )
        self.assertEqual(400, status)
        self.assertIn("cannot be overridden", payload["detail"])

    def test_copilot_chat_rejects_unknown_fields(self):
        status, payload = self.request(
            "POST",
            "/v1/copilot/chat",
            {"message": "hello", "unexpected": True},
            headers={"X-Research-OS-Session": self.issue_session("frank")},
        )
        self.assertEqual(400, status)
        self.assertIn("unsupported copilot chat fields", payload["detail"])

    @patch("server.copilot_service.CopilotChatClient")
    def test_copilot_chat_gateway_failures_return_502(self, client_cls):
        client_cls.return_value.chat.side_effect = server.copilot_service.CopilotChatError(
            "gateway unavailable"
        )
        with patch.dict(
            os.environ,
            {"RESEARCH_OS_COPILOT_AUDIT_DIR": tempfile.gettempdir()},
            clear=False,
        ):
            status, payload = self.request(
                "POST",
                "/v1/copilot/chat",
                {"message": "hello"},
                headers={"X-Research-OS-Session": self.issue_session("dave")},
            )
        self.assertEqual(502, status)
        self.assertEqual("copilot_error", payload["error"])


if __name__ == "__main__":
    unittest.main()
