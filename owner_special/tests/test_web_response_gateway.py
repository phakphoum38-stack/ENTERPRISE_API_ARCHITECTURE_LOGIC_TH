from __future__ import annotations

import unittest
from unittest.mock import patch

from owner_special.research_os_friend.catalog import install_builtin_tools
from owner_special.research_os_friend.models import FriendRequest
from owner_special.research_os_friend.runtime import FriendRuntime
from owner_special.research_os_friend.tools import ToolRegistry
from v3.research_os_v3.research_tools import ToolResult


class WebResponseGatewayTests(unittest.TestCase):
    def test_web_tool_is_registered(self) -> None:
        registry = install_builtin_tools(ToolRegistry())
        self.assertIn("web.fetch", registry.names())

    def test_web_request_is_auto_routed(self) -> None:
        runtime = FriendRuntime.create_owner_special("owner")
        request = FriendRequest(
            owner_id="owner",
            profile_id="default",
            session_id="web-test",
            text="อ่านโครงสร้างเว็บไซต์ https://example.com ให้หน่อย",
        )
        with patch("owner_special.research_os_friend.web_tool.urlopen") as mocked:
            response = mocked.return_value
            response.headers.get.return_value = "text/html"
            response.read.return_value = b"<html><head><title>Example</title></head><body><h1>Hello</h1><a href='/docs'>Docs</a></body></html>"
            result = runtime.ask(request)
        self.assertIn("web.fetch", result.decision.selected_tools)
        self.assertEqual(result.metadata["tool_results"]["web.fetch"]["title"], "Example")
        self.assertIn("Verified tool results", result.text)
        mocked.assert_called_once()

    def test_v3_web_tool_remains_explicit(self) -> None:
        runtime = FriendRuntime.create_owner_special("owner")
        request = FriendRequest(
            owner_id="owner",
            profile_id="default",
            session_id="v3",
            text="fetch",
            requested_tools=("web",),
        )
        with patch("v3.research_os_v3.network_research_tools.urlopen") as mocked:
            response = mocked.return_value.__enter__.return_value
            response.headers.get.return_value = "text/html"
            response.read.return_value = b"<html><title>Example</title></html>"
            result = runtime.execute_v3(request, capability="web.fetch", input={"url": "https://example.com"})
        self.assertIsInstance(result, ToolResult)
        self.assertTrue(result.success)
        mocked.assert_called_once()


if __name__ == "__main__":
    unittest.main()
