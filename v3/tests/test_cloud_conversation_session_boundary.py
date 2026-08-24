import json
import os
import sys
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "research_os_api"))

from tools.research_os_api import server
from tools.research_os_api.auth_session import issue_session, revoke_session


class CloudConversationSessionBoundaryTests(unittest.TestCase):
    def setUp(self):
        self._old_env = {
            key: os.environ.get(key)
            for key in ("RESEARCH_OS_SESSION_SECRET", "RESEARCH_OS_V3_DATA_DIR", "RESEARCH_OS_SYNC_KEY")
        }
        os.environ["RESEARCH_OS_SESSION_SECRET"] = "test-cloud-session-boundary-secret"
        os.environ["RESEARCH_OS_V3_DATA_DIR"] = tempfile.mkdtemp(prefix="research-os-cloud-test-")
        os.environ["RESEARCH_OS_SYNC_KEY"] = "test-sync-key"
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.ResearchOSHandler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=2)
        for key, value in self._old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def request(self, method, path, token=None, body=None, sync_key=None):
        host, port = self.httpd.server_address
        conn = HTTPConnection(host, port, timeout=5)
        headers = {"Content-Type": "application/json"}
        if token:
            headers["X-Research-OS-Session"] = token
        if sync_key:
            headers["X-Research-OS-Sync-Key"] = sync_key
        payload = None if body is None else json.dumps(body).encode()
        conn.request(method, path, body=payload, headers=headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return response.status, json.loads(data.decode() or "{}")

    def test_sync_key_only_is_denied(self):
        status, payload = self.request("GET", "/v1/conversations/cloud", sync_key="test-sync-key")
        self.assertEqual(401, status)
        self.assertEqual("invalid_session", payload["error"])

    def test_missing_sync_key_is_denied_even_with_session(self):
        token = issue_session({"sub": "alice", "email": "alice@example.com"})
        status, payload = self.request("GET", "/v1/conversations/cloud", token=token)
        self.assertEqual(401, status)
        self.assertEqual("invalid_sync_key", payload["error"])

    def test_alice_and_bob_are_isolated_for_read_write_delete(self):
        alice = issue_session({"sub": "alice", "email": "alice@example.com"})
        bob = issue_session({"sub": "bob", "email": "bob@example.com"})
        status, _ = self.request(
            "POST", "/v1/conversations/cloud/sync", token=alice, sync_key="test-sync-key",
            body={"session": {"id": "alice-chat", "title": "Alice", "updated_at": 10, "messages": []}},
        )
        self.assertEqual(200, status)
        status, payload = self.request("GET", "/v1/conversations/cloud", token=bob, sync_key="test-sync-key")
        self.assertEqual(200, status)
        self.assertEqual([], payload["sessions"])
        status, payload = self.request("GET", "/v1/conversations/cloud", token=alice, sync_key="test-sync-key")
        self.assertEqual(200, status)
        self.assertEqual(["alice-chat"], [item["id"] for item in payload["sessions"]])
        status, payload = self.request(
            "POST", "/v1/conversations/cloud/delete", token=bob, sync_key="test-sync-key",
            body={"session_id": "alice-chat"},
        )
        self.assertEqual(200, status)
        self.assertFalse(payload["deleted"])
        status, payload = self.request("GET", "/v1/conversations/cloud", token=alice, sync_key="test-sync-key")
        self.assertEqual(200, status)
        self.assertEqual(["alice-chat"], [item["id"] for item in payload["sessions"]])
        status, payload = self.request(
            "POST", "/v1/conversations/cloud/delete", token=alice, sync_key="test-sync-key",
            body={"session_id": "alice-chat"},
        )
        self.assertEqual(200, status)
        self.assertTrue(payload["deleted"])

    def test_revoked_session_is_denied_while_other_user_remains_valid(self):
        alice = issue_session({"sub": "alice", "email": "alice@example.com"})
        bob = issue_session({"sub": "bob", "email": "bob@example.com"})
        revoke_session(alice)
        status, payload = self.request("GET", "/v1/conversations/cloud", token=alice, sync_key="test-sync-key")
        self.assertEqual(401, status)
        self.assertEqual("invalid_session", payload["error"])
        status, _ = self.request("GET", "/v1/conversations/cloud", token=bob, sync_key="test-sync-key")
        self.assertEqual(200, status)


if __name__ == "__main__":
    unittest.main()
