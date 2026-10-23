"""Security regression tests for the authenticated GitHub dashboard endpoint."""

import os
import unittest
from unittest.mock import patch

from server import ResearchOSHandler


class FakeDashboardHandler(ResearchOSHandler):
    def __init__(self, path, headers):
        self.path = path
        self.headers = headers
        self.response = None

    def _send(self, status, payload):
        self.response = (int(status), payload)


class GitHubDashboardAuthorizationTests(unittest.TestCase):
    def test_missing_session_is_401(self):
        handler = FakeDashboardHandler("/v1/github/dashboard", {})
        with patch("server.require_session", side_effect=ValueError("missing")):
            handler.do_GET()
        self.assertEqual(handler.response[0], 401)
        self.assertEqual(handler.response[1]["error"], "authentication_required")

    def test_non_owner_is_403(self):
        handler = FakeDashboardHandler("/v1/github/dashboard", {})
        with patch("server.require_session", return_value={"role": "user"}):
            handler.do_GET()
        self.assertEqual(handler.response[0], 403)
        self.assertEqual(handler.response[1]["error"], "owner_authorization_required")

    def test_repository_outside_allowlist_is_403(self):
        handler = FakeDashboardHandler(
            "/v1/github/dashboard?repository=attacker/private-repo", {}
        )
        env = {
            "RESEARCH_OS_GITHUB_REPOSITORY": "phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH",
            "RESEARCH_OS_GITHUB_ALLOWED_REPOSITORIES": "phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH",
        }
        with patch.dict(os.environ, env, clear=False), patch(
            "server.require_session", return_value={"role": "owner"}
        ), patch("server.github_dashboard") as dashboard:
            handler.do_GET()
        self.assertEqual(handler.response[0], 403)
        self.assertEqual(handler.response[1]["error"], "repository_not_allowed")
        dashboard.assert_not_called()

    def test_owner_can_read_only_allowlisted_repository(self):
        repository = "phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH"
        handler = FakeDashboardHandler("/v1/github/dashboard", {})
        payload = {"repository": repository, "read_only": True}
        env = {
            "RESEARCH_OS_GITHUB_REPOSITORY": repository,
            "RESEARCH_OS_GITHUB_ALLOWED_REPOSITORIES": repository,
        }
        with patch.dict(os.environ, env, clear=False), patch(
            "server.require_session", return_value={"role": "owner"}
        ), patch("server.github_dashboard", return_value=payload) as dashboard:
            handler.do_GET()
        self.assertEqual(handler.response, (200, payload))
        dashboard.assert_called_once_with(repository)

    def test_provider_errors_are_redacted(self):
        handler = FakeDashboardHandler("/v1/github/dashboard", {})
        env = {
            "RESEARCH_OS_GITHUB_REPOSITORY": "phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH",
            "RESEARCH_OS_GITHUB_ALLOWED_REPOSITORIES": "phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH",
        }
        with patch.dict(os.environ, env, clear=False), patch(
            "server.require_session", return_value={"role": "owner"}
        ), patch("server.github_dashboard", side_effect=__import__("github_status").GitHubStatusError("sensitive upstream detail")):
            handler.do_GET()
        self.assertEqual(handler.response[0], 502)
        self.assertEqual(handler.response[1], {"error": "github_provider_unavailable"})
        self.assertNotIn("sensitive", str(handler.response))


if __name__ == "__main__":
    unittest.main()
