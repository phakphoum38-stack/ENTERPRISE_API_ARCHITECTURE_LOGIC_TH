import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
API_DIR = ROOT / "tools" / "research_os_api"
sys.path.insert(0, str(API_DIR))

import auth_session  # noqa: E402
import server  # noqa: E402


class _FakeGoogleIdentityBroker:
    def disconnect(self):
        return {"signed_out": True}


class ResearchOSSignoutRevocationTests(unittest.TestCase):
    def setUp(self):
        self.previous_secret = os.environ.get("RESEARCH_OS_SESSION_SECRET")
        os.environ["RESEARCH_OS_SESSION_SECRET"] = "test-only-research-os-session-secret"
        self.previous_data_dir = os.environ.get("RESEARCH_OS_V3_DATA_DIR")
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["RESEARCH_OS_V3_DATA_DIR"] = self.tmp.name
        self.httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.ResearchOSHandler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=2)
        self.tmp.cleanup()
        if self.previous_secret is None:
            os.environ.pop("RESEARCH_OS_SESSION_SECRET", None)
        else:
            os.environ["RESEARCH_OS_SESSION_SECRET"] = self.previous_secret
        if self.previous_data_dir is None:
            os.environ.pop("RESEARCH_OS_V3_DATA_DIR", None)
        else:
            os.environ["RESEARCH_OS_V3_DATA_DIR"] = self.previous_data_dir

    def _signout(self, token):
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.httpd.server_port}/v1/auth/google/signout",
            data=b"{}",
            headers={"Content-Type": "application/json", "Cookie": f"research_os_session={token}"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=3) as response:
            return response.status, response.headers, response.read()

    def test_signout_revokes_cookie_session_and_preserves_other_user(self):
        alice = auth_session.issue_session({"email": "alice@example.test", "sub": "alice", "role": "user"})
        bob = auth_session.issue_session({"email": "bob@example.test", "sub": "bob", "role": "user"})

        with patch.object(server, "GoogleIdentityBroker", _FakeGoogleIdentityBroker):
            status, headers, body = self._signout(alice)

        self.assertEqual(status, 200)
        self.assertEqual(body, b'{\n  "signed_out": true\n}')
        self.assertIn("research_os_session=;", headers.get("Set-Cookie", ""))
        with self.assertRaises(ValueError):
            auth_session.verify_session(alice)
        self.assertEqual(auth_session.verify_session(bob)["user_id"], "bob")

    def test_signout_without_session_remains_compatible(self):
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.httpd.server_port}/v1/auth/google/signout",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with patch.object(server, "GoogleIdentityBroker", _FakeGoogleIdentityBroker):
            with urllib.request.urlopen(request, timeout=3) as response:
                self.assertEqual(response.status, 200)
                self.assertIn("research_os_session=;", response.headers.get("Set-Cookie", ""))


if __name__ == "__main__":
    unittest.main()
