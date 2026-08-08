#!/usr/bin/env python3
from __future__ import annotations

import json
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

from streaming_handler import StreamingResearchOSHandler


class StreamingHandlerTest(unittest.TestCase):
    def _start_server(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), StreamingResearchOSHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, thread

    def test_mock_provider_streams_ndjson(self) -> None:
        server, thread = self._start_server()
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
            self.assertEqual(events[-1]["metrics"]["output_chars"], len(text))
            self.assertGreaterEqual(events[-1]["metrics"]["elapsed_ms"], 0)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_provider_capabilities_are_secret_safe(self) -> None:
        server, thread = self._start_server()
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{server.server_port}/v1/providers/capabilities",
                timeout=5,
            ) as response:
                payload = json.loads(response.read().decode("utf-8"))

            providers = {item["provider"]: item for item in payload["providers"]}
            self.assertTrue(payload["safe"])
            self.assertIn("gemini", providers)
            self.assertTrue(providers["gemini"]["native_streaming"])
            self.assertIn("ollama", providers)
            self.assertTrue(providers["ollama"]["local_capable"])
            self.assertNotIn("api_key", json.dumps(payload).lower())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
