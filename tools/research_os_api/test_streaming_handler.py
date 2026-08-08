#!/usr/bin/env python3
from __future__ import annotations

import json
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

from streaming_handler import StreamingResearchOSHandler


class StreamingHandlerTest(unittest.TestCase):
    def test_mock_provider_streams_ndjson(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), StreamingResearchOSHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            payload = json.dumps(
                {
                    "provider": "mock",
                    "prompt": "hello streaming",
                    "memory": False,
                    "chunk_size": 5,
                }
            ).encode("utf-8")
            request = urllib.request.Request(
                f"http://127.0.0.1:{server.server_port}/v1/ai/stream",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                self.assertEqual(response.status, 200)
                self.assertIn("application/x-ndjson", response.headers.get("Content-Type", ""))
                events = [
                    json.loads(line.decode("utf-8"))
                    for line in response.readlines()
                    if line.strip()
                ]

            self.assertEqual(events[0]["type"], "meta")
            self.assertEqual(events[-1]["type"], "done")
            text = "".join(event.get("text", "") for event in events if event["type"] == "delta")
            self.assertEqual(text, "MOCK: hello streaming")
            self.assertEqual(events[-1]["provider"], "mock")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
