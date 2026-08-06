import json
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

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

    def request(self, method: str, path: str, payload=None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_health(self):
        status, payload = self.request("GET", "/health")
        self.assertEqual(200, status)
        self.assertEqual("ok", payload["status"])

    def test_mock_provider_generation(self):
        status, payload = self.request("POST", "/v1/ai/generate", {
            "provider": "mock",
            "prompt": "วิเคราะห์แนวคิดนี้",
        })
        self.assertEqual(200, status)
        self.assertEqual("mock", payload["provider"])
        self.assertIn("วิเคราะห์", payload["text"])

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

    def test_provider_list(self):
        status, payload = self.request("GET", "/v1/providers")
        self.assertEqual(200, status)
        self.assertIn("mock", payload["providers"])
        self.assertIn("anthropic", payload["providers"])


if __name__ == "__main__":
    unittest.main()
