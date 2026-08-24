import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from tools.research_os_api import server
from tools.research_os_api.auth_session import issue_session


class SignoutRevocationHttpTests(unittest.TestCase):
    def setUp(self):
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.ResearchOSHandler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.httpd.server_address[1]

    def tearDown(self):
        self.httpd.shutdown()
        self.thread.join(timeout=2)
        self.httpd.server_close()

    def request(self, method, path, token=None):
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
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
        session_a = issue_session("owner-a")
        session_b = issue_session("owner-b")

        with patch.object(server.GoogleIdentityBroker, "disconnect", return_value={"disconnected": True}):
            status, _, set_cookie = self.request(
                "POST", "/v1/auth/google/signout", session_a.token
            )

        self.assertEqual(status, 200)
        self.assertIn("research_os_session=;", set_cookie or "")

        # The canonical protected boundary must reject the revoked token.
        status, _, _ = self.request("GET", "/v1/agents/readiness", session_a.token)
        self.assertEqual(status, 401)

        # A different session must not be revoked as a side effect.
        status, _, _ = self.request("GET", "/v1/agents/readiness", session_b.token)
        self.assertEqual(status, 200)


if __name__ == "__main__":
    unittest.main()
