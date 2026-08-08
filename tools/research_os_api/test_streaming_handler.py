#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from memory_engine import MemoryEngine, JsonMemoryStore
from streaming_handler import StreamingResearchOSHandler


class StreamingHandlerTest(unittest.TestCase):
    def _start_server(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), StreamingResearchOSHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, thread

    def _stream(self, server, payload):
        request = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}/v1/ai/stream",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            self.assertEqual(response.status, 200)
            self.assertIn("application/x-ndjson", response.headers.get("Content-Type", ""))
            return [
                json.loads(line.decode("utf-8"))
                for line in response.readlines()
                if line.strip()
            ]

    def test_mock_provider_streams_ndjson(self) -> None:
        server, thread = self._start_server()
        try:
            events = self._stream(
                server,
                {
                    "provider": "mock",
                    "prompt": "hello streaming",
                    "memory": False,
                    "chunk_size": 5,
                },
            )
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

    def test_completed_stream_can_capture_local_runtime_memory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store_path = Path(directory) / "records.json"
            with patch.dict(os.environ, {"RESEARCH_OS_MEMORY_STORE": str(store_path)}):
                server, thread = self._start_server()
                try:
                    events = self._stream(
                        server,
                        {
                            "provider": "mock",
                            "prompt": "remember this chat",
                            "memory": False,
                            "capture_memory": True,
                            "session_id": "session-test",
                        },
                    )
                    done = events[-1]
                    self.assertTrue(done["memory_capture"])
                    self.assertEqual(len(done["captured_memory_ids"]), 2)

                    records = MemoryEngine(JsonMemoryStore(store_path)).timeline(
                        session_id="session-test"
                    )
                    self.assertEqual(len(records), 2)
                    roles = {record.metadata.get("role") for record in records}
                    self.assertEqual(roles, {"user", "assistant"})
                    self.assertTrue(all(record.source == "chat" for record in records))
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
