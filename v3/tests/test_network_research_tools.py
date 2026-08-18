from __future__ import annotations

import unittest
from unittest.mock import patch

from research_os_v3.network_research_tools import GitHubResearchTool, WebResearchTool
from research_os_v3.research_tools import ToolRequest


class NetworkResearchToolTests(unittest.TestCase):
    def test_web_rejects_invalid_url(self) -> None:
        result = WebResearchTool().execute(ToolRequest("web.fetch", {"url": "file:///etc/passwd"}))
        self.assertFalse(result.success)
        self.assertEqual(result.error, "InvalidUrl")

    def test_github_rejects_invalid_repo(self) -> None:
        result = GitHubResearchTool().execute(ToolRequest("github.repository", {"owner": "a/b", "repo": "x"}))
        self.assertFalse(result.success)
        self.assertEqual(result.error, "InvalidRepository")

    def test_github_repository_uses_public_api(self) -> None:
        tool = GitHubResearchTool()
        with patch.object(tool, "_get_json", return_value={"full_name": "octo/research"}) as fetch:
            result = tool.execute(ToolRequest("github.repository", {"owner": "octo", "repo": "research"}))
        self.assertTrue(result.success)
        self.assertEqual(result.output["full_name"], "octo/research")
        self.assertEqual(result.metadata["provider"], "github-api")
        fetch.assert_called_once()


if __name__ == "__main__":
    unittest.main()
