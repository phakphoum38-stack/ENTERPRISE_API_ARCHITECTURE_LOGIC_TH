import json
import os
import tempfile
import threading
import unittest
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from streaming_handler import StreamingResearchOSHandler


class RuntimeMemoryApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(
            os.environ,
            {"RESEARCH_OS_MEMORY_STORE": os.path.join(self.temp.name, "records.json")},
            clear=False,
        )
        self.env.start()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), StreamingResearchOSHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.env.stop()
        self.temp.cleanup()

    def _json_request(self, path: str, *, method: str = "GET", body=None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            self.base + path,
            data=data,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_runtime_memory_crud_search_and_timeline(self) -> None:
        status, created = self._json_request(
            "/v1/runtime-memory",
            method="POST",
            body={
                "type": "conversation",
                "title": "Memory API",
                "content": "Research OS runtime memory integration",
                "project_id": "research-os",
                "session_id": "session-1",
                "tags": ["memory", "api"],
                "priority": 7,
            },
        )
        self.assertEqual(status, 201)
        memory_id = created["record"]["id"]

        query = urllib.parse.urlencode({"q": "memory", "project_id": "research-os"})
        status, search = self._json_request(f"/v1/runtime-memory/search?{query}")
        self.assertEqual(status, 200)
        self.assertEqual(search["count"], 1)
        self.assertEqual(search["hits"][0]["record"]["id"], memory_id)

        status, timeline = self._json_request(
            "/v1/runtime-memory/timeline?session_id=session-1"
        )
        self.assertEqual(status, 200)
        self.assertEqual(timeline["count"], 1)
        self.assertEqual(timeline["records"][0]["id"], memory_id)

        status, updated = self._json_request(
            f"/v1/runtime-memory/{memory_id}/update",
            method="POST",
            body={"content": "updated runtime memory", "tags": ["updated"]},
        )
        self.assertEqual(status, 200)
        self.assertEqual(updated["record"]["content"], "updated runtime memory")

        status, deleted = self._json_request(
            f"/v1/runtime-memory/{memory_id}",
            method="DELETE",
        )
        self.assertEqual(status, 200)
        self.assertTrue(deleted["deleted"])

        status, records = self._json_request("/v1/runtime-memory")
        self.assertEqual(status, 200)
        self.assertEqual(records["count"], 0)


if __name__ == "__main__":
    unittest.main()
