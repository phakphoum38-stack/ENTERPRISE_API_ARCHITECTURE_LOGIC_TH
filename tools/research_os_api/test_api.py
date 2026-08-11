import io
import json
import os
import tempfile
import threading
import unittest
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import server


class ResearchOSAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
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
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_health(self):
        status, payload = self.request("GET", "/health")
        self.assertEqual(200, status)
        self.assertEqual("ok", payload["status"])
        self.assertTrue(payload["memory"])

    def test_mock_provider_generation(self):
        status, payload = self.request("POST", "/v1/ai/generate", {
            "provider": "mock",
            "prompt": "วิเคราะห์แนวคิดนี้",
        })
        self.assertEqual(200, status)
        self.assertEqual("mock", payload["provider"])
        self.assertIn("วิเคราะห์", payload["text"])

    def test_memory_search(self):
        query = urllib.parse.quote("conversation knowledge")
        status, payload = self.request("GET", f"/v1/memory/search?q={query}&limit=3")
        self.assertEqual(200, status)
        self.assertGreaterEqual(payload["count"], 1)
        self.assertIn("artifact_id", payload["hits"][0])
        self.assertIn("score", payload["hits"][0])

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

    def test_oauth_callback_request_log_redacts_query_secrets(self):
        handler = object.__new__(server.ResearchOSHandler)
        handler.path = "/v1/google-workspace/oauth/callback?code=secret-code&state=secret-state"
        handler.command = "GET"
        handler.request_version = "HTTP/1.1"
        sink = io.StringIO()

        with patch.object(server.sys, "stderr", sink):
            handler.log_request(200, 12)

        log_line = sink.getvalue()
        self.assertIn("/v1/google-workspace/oauth/callback?[REDACTED]", log_line)
        self.assertNotIn("secret-code", log_line)
        self.assertNotIn("secret-state", log_line)
        self.assertNotIn("code=", log_line)
        self.assertNotIn("state=", log_line)

    def test_google_workspace_local_accept_enables_app_access(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {"RESEARCH_OS_DATA_DIR": tmp},
            clear=True,
        ):
            status, payload = self.request("POST", "/v1/google-workspace/local/accept", {})
            self.assertEqual(200, status)
            self.assertTrue(payload["app_access"])
            self.assertTrue(payload["local_account_accepted"])
            self.assertEqual(payload["account_mode"], "local")
            self.assertFalse(payload["connected"])


if __name__ == "__main__":
    unittest.main()
