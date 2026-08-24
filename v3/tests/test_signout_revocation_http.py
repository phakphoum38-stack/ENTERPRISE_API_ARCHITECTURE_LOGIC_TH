import os
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from tools.research_os_api import agent_server, server
from tools.research_os_api.auth_session import issue_session


class SignoutRevocationHttpTests(unittest.TestCase):
    def setUp(self):
        self._env = {
            "RESEARCH_OS_SESSION_SECRET": "test-signout-revocation-secret",
            "RESEARCH_OS_V3_DATA_DIR": tempfile.mkdtemp(prefix="research-os-session-test-"),
        }
        self._old_env = {key: os.environ.get(key) for key in self._env}
        os.environ.update(self._env)

        self.api_httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.ResearchOSHandler)
        self.agent_httpd = ThreadingHTTPServer(("127.0.0.1", 0), agent_server.AgentResearchOSHandler)
        self.threads = [
            threading.Thread(target=self.api_httpd.serve_forever, daemon=True),
            threading.Thread(target=self.agent_httpd.serve_forever, daemon=True),
        ]
        for thread in self.threads:
            thread.start()

    def tearDown(self):
        for httpd in (self.api_httpd, self.agent_httpd):
            httpd.shutdown()
            httpd.server_close()
        for thread in self.threads:
            thread.join(timeout=2)
        for key, value in self._old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    @staticmethod
    def request(httpd, method, path, token=None):
        host, port = httpd.server_address
        conn = HTTPConnection(host, port, timeout=5)
        headers = {}
        if token:
            headers["X-Research-OS-Session"] = token
        conn.request(method, path, headers=headers)
        response = conn.getresponse()
        body = response.read()
        set_cookie = response.getheader("Set-Cookie")
        conn.close()
        return response.status, body, set_cookie

    def test_signout_revokes_session_and_clears_cookie(self):
        session_a = issue_session({"sub": "owner-a", "email": "a@example.com"})
        session_b = issue_session({"sub": "owner-b", "email": "b@example.com"})

        # Establish that both sessions are accepted before signout.
        status, _, _ = self.request(self.agent_httpd, "GET", "/v1/agents/readiness", session_a)
        self.assertEqual(status, 200)
        status, _, _ = self.request(self.agent_httpd, "GET", "/v1/agents/readiness", session_b)
        self.assertEqual(status, 200)

        with patch.object(server.GoogleIdentityBroker, "disconnect", return_value={"disconnected": True}):
            status, _, set_cookie = self.request(
                self.api_httpd, "POST", "/v1/auth/google/signout", session_a
            )

        self.assertEqual(status, 200)
        self.assertIn("research_os_session=;", set_cookie or "")

        # Canonical protected boundary must reject the revoked session.
        status, _, _ = self.request(self.agent_httpd, "GET", "/v1/agents/readiness", session_a)
        self.assertEqual(status, 401)

        # Independent session must remain valid.
        status, _, _ = self.request(self.agent_httpd, "GET", "/v1/agents/readiness", session_b)
        self.assertEqual(status, 200)


if __name__ == "__main__":
    unittest.main()
