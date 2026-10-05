from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from research_os_friend.models import FriendRequest
from research_os_friend.runtime import FriendRuntime
from tools.research_os_api.auth_session import issue_session
from v3.research_os_v3.research_tools import ToolResult


class V3ExecutionAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self._previous_secret = os.environ.get("RESEARCH_OS_SESSION_SECRET")
        os.environ["RESEARCH_OS_SESSION_SECRET"] = "owner-special-v3-test-secret"

    def tearDown(self) -> None:
        if self._previous_secret is None:
            os.environ.pop("RESEARCH_OS_SESSION_SECRET", None)
        else:
            os.environ["RESEARCH_OS_SESSION_SECRET"] = self._previous_secret

    def make_runtime(self) -> tuple[FriendRuntime, tempfile.TemporaryDirectory[str]]:
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        return (
            FriendRuntime.create_owner_special(
                "owner-test",
                data_root=root,
                repository_root=root,
            ),
            tmp,
        )

    def test_v3_adapter_registers_local_and_network_tools(self) -> None:
        runtime, tmp = self.make_runtime()
        self.addCleanup(tmp.cleanup)

        self.assertEqual(runtime.v3.names(), ("file", "github", "python", "shell", "web"))
        rows = {row["name"]: row for row in runtime.tool_catalog()}
        for name in ("web", "github", "file", "python", "shell"):
            self.assertEqual(rows[name]["state"], "implemented_unregistered")

    def test_v3_adapter_executes_python_without_network(self) -> None:
        runtime, tmp = self.make_runtime()
        self.addCleanup(tmp.cleanup)
        request = FriendRequest(
            owner_id="owner-test",
            text="analyze python",
            requested_tools=("python",),
        )

        session_token = issue_session({"user_id": "owner-test", "email": "owner-test@research-os.local", "role": "owner"})
        result = runtime.execute_v3(
            request,
            capability="python.analyze",
            input={"source": "import json\nvalue = 1"},
            session_token=session_token,
        )

        self.assertIsInstance(result, ToolResult)
        self.assertTrue(result.success)
        self.assertEqual(result.output["imports"], ["json"])

    def test_v3_adapter_rejects_unrequested_capability(self) -> None:
        runtime, tmp = self.make_runtime()
        self.addCleanup(tmp.cleanup)
        session_token = issue_session({"user_id": "owner-test", "email": "owner-test@research-os.local", "role": "owner"})
        request = FriendRequest(owner_id="owner-test", text="run", requested_tools=(), session_token=session_token)

        with self.assertRaisesRegex(PermissionError, "explicitly requested"):
            runtime.execute_v3(
                request,
                capability="python.analyze",
                input={"source": "value = 1"},
            )

    def test_v3_adapter_rejects_wrong_owner(self) -> None:
        runtime, tmp = self.make_runtime()
        self.addCleanup(tmp.cleanup)
        session_token = issue_session({"user_id": "owner-test", "email": "owner-test@research-os.local", "role": "owner"})
        request = FriendRequest(
            owner_id="other-owner",
            text="analyze python",
            requested_tools=("python",),
            session_token=session_token,
        )

        with self.assertRaisesRegex(PermissionError, "Owner Special request"):
            runtime.execute_v3(
                request,
                capability="python.analyze",
                input={"source": "value = 1"},
            )


if __name__ == "__main__":
    unittest.main()
