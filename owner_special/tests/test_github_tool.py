from __future__ import annotations

import unittest
from unittest.mock import patch

from research_os_friend.runtime import FriendRuntime


class GitHubToolTests(unittest.TestCase):
    def test_github_repository_tool_is_registered(self) -> None:
        runtime = FriendRuntime.create_owner_special("phakphum")
        self.assertIn("github.repository_status", runtime.orchestrator.tools.names())

    @patch("research_os_friend.catalog.github_dashboard")
    def test_github_request_is_auto_routed(self, dashboard) -> None:
        dashboard.return_value = {
            "repository": "phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH",
            "default_branch": "main",
            "visibility": "public",
            "url": "https://github.com/phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH",
            "open_issues_count": 0,
            "pull_requests": [],
            "workflow_runs": [],
            "artifacts": [],
            "credential_configured": False,
        }
        runtime = FriendRuntime.create_owner_special("phakphum")
        response = runtime.ask(
            __import__("research_os_friend.models", fromlist=["FriendRequest"]).FriendRequest(
                owner_id="phakphum",
                text="ตรวจสอบ repository phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH",
            )
        )
        self.assertIn("github.repository_status", response.decision.selected_tools)
        self.assertEqual(response.metadata["tool_results"]["github.repository_status"]["default_branch"], "main")
        dashboard.assert_called_once_with("phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH")


if __name__ == "__main__":
    unittest.main()
