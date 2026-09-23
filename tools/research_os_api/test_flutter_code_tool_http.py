from __future__ import annotations

import http.client
import json
import os
import tempfile
import threading
import time
import unittest
from unittest import mock
import uuid
from http.server import ThreadingHTTPServer
from pathlib import Path

from developer_identity import IdentityAssertionVerifier
from developer_server import DeveloperPlatformHandler


class FlutterCodeToolHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        project = root / "apps" / "research_os_flutter" / "lib"
        project.mkdir(parents=True)
        (project / "main.dart").write_text("void main() {}\n", encoding="utf-8")
        self.old = {name: os.environ.get(name) for name in (
            "RESEARCH_OS_DATA_DIR",
            "RESEARCH_OS_IDENTITY_PROXY_SECRET",
            "RESEARCH_OS_CODE_ROOT",
            "RESEARCH_OS_CODE_OWNER_IDS",
        )}
        os.environ.update({
            "RESEARCH_OS_DATA_DIR": str(root / "data"),
            "RESEARCH_OS_IDENTITY_PROXY_SECRET": "test-secret-0123456789",
            "RESEARCH_OS_CODE_ROOT": str(root),
            "RESEARCH_OS_CODE_OWNER_IDS": "user:owner",
        })
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), DeveloperPlatformHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        for name, value in self.old.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        self.temp.cleanup()

    def request(self, method: str, path: str, principal: str, body: dict | None = None):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_address[1], timeout=5)
        issued_at = int(time.time())
        nonce = uuid.uuid4().hex
        signature = IdentityAssertionVerifier("test-secret-0123456789").signature_for(principal, issued_at, nonce)
        headers = {
            "Content-Type": "application/json",
            "X-ResearchOS-Principal": principal,
            "X-ResearchOS-Identity-Timestamp": str(issued_at),
            "X-ResearchOS-Identity-Nonce": nonce,
            "X-ResearchOS-Identity-Signature": signature,
        }
        conn.request(method, path, body=json.dumps(body or {}), headers=headers)
        response = conn.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
        status = response.status
        conn.close()
        return status, payload

    def test_full_owner_code_lifecycle(self) -> None:
        status, projects = self.request("GET", "/v2/developer/code/projects", "user:owner")
        self.assertEqual(status, 200)
        self.assertIn("research_os_flutter", projects["projects"])

        status, files = self.request("GET", "/v2/developer/code/files?project=research_os_flutter", "user:owner")
        self.assertEqual(status, 200)
        self.assertEqual(files["items"][0]["path"], "lib/main.dart")

        status, current = self.request("GET", "/v2/developer/code/file/lib%2Fmain.dart?project=research_os_flutter", "user:owner")
        self.assertEqual(status, 200)
        sha = current["sha256"]

        new_content = "void main() { print(1); }\n"
        status, diff = self.request("POST", "/v2/developer/code/preview", "user:owner", {
            "project": "research_os_flutter",
            "path": "lib/main.dart",
            "original_sha256": sha,
            "content": new_content,
        })
        self.assertEqual(status, 200)
        self.assertTrue(diff["changed"])

        with mock.patch("flutter_code_tool.validate", return_value={"ok": True, "steps": []}):
            status, applied = self.request("POST", "/v2/developer/code/apply", "user:owner", {
                "project": "research_os_flutter",
                "path": "lib/main.dart",
                "original_sha256": sha,
                "content": new_content,
            })
        self.assertEqual(status, 200)
        self.assertTrue(applied["applied"])

    def test_non_owner_cannot_apply(self) -> None:
        status, current = self.request("GET", "/v2/developer/code/file/lib%2Fmain.dart?project=research_os_flutter", "user:developer")
        self.assertEqual(status, 200)
        status, denied = self.request("POST", "/v2/developer/code/apply", "user:developer", {
            "project": "research_os_flutter",
            "path": "lib/main.dart",
            "original_sha256": current["sha256"],
            "content": "changed\n",
        })
        self.assertEqual(status, 403)
        self.assertEqual(denied["error"]["code"], "permission_denied")


if __name__ == "__main__":
    unittest.main()
