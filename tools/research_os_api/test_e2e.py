import json
import os
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

from server import ResearchOSHandler


class ResearchOSEndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous_ai_route = os.environ.get("RESEARCH_OS_AI_ROUTE")
        os.environ["RESEARCH_OS_AI_ROUTE"] = "direct-provider"
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), ResearchOSHandler)
        cls.base_url = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)
        if cls.previous_ai_route is None:
            os.environ.pop("RESEARCH_OS_AI_ROUTE", None)
        else:
            os.environ["RESEARCH_OS_AI_ROUTE"] = cls.previous_ai_route

    def request_json(self, path, payload=None):
        data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST" if payload is not None else "GET",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_living_house_flow(self):
        with urllib.request.urlopen(self.base_url + "/", timeout=5) as response:
            html = response.read().decode("utf-8")
        self.assertIn("ยินดีต้อนรับกลับครับเพื่อน", html)
        self.assertIn("เริ่มงาน", html)

        status, health = self.request_json("/health")
        self.assertEqual(status, 200)
        self.assertTrue(health["ui"])

        session_id = "e2e-session"
        status, generated = self.request_json(
            "/v1/ai/generate",
            {
                "provider": "mock",
                "prompt": "ช่วยสรุปภารกิจของบ้าน",
                "session_id": session_id,
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(generated["provider"], "mock")
        self.assertEqual(generated["session_id"], session_id)
        self.assertTrue(generated["text"])

        status, captured = self.request_json(
            "/v1/conversations/analyze",
            {
                "conversation": [
                    {"role": "user", "content": "เราควรสร้าง Entrance UI และเชื่อม API"},
                    {"role": "assistant", "content": generated["text"]},
                ],
                "title": "E2E Session",
                "tags": ["e2e"],
                "min_quality": 20,
            },
        )
        self.assertEqual(status, 200)
        self.assertIn("artifact", captured)
        self.assertFalse(captured["persisted"])


if __name__ == "__main__":
    unittest.main()
