from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from research_os_friend.models import FriendRequest
from research_os_friend.runtime import FriendRuntime
from v3.research_os_v3.research_tools import ToolResult


class V3ExecutionAdapterTests(unittest.TestCase):
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
            self.assertEqual(rows[name]["state"], "ready")

    def test_v3_adapter_executes_python_without_network(self) -> None:
        runtime, tmp = self.make_runtime()
        self.addCleanup(tmp.cleanup)
        request = FriendRequest(
            owner_id="owner-test",
            text="analyze python",
            requested_tools=("python",),
        )

        result = runtime.execute_v3(
            request,
            capability="python.analyze",
            input={"source": "import json\nvalue = 1"},
        )

        self.assertIsInstance(result, ToolResult)
        self.assertTrue(result.success)
        self.assertEqual(result.output["imports"], ["json"])

    def test_v3_adapter_rejects_unrequested_capability(self) -> None:
        runtime, tmp = self.make_runtime()
        self.addCleanup(tmp.cleanup)
        request = FriendRequest(owner_id="owner-test", text="run", requested_tools=())

        with self.assertRaisesRegex(PermissionError, "explicitly requested"):
            runtime.execute_v3(
                request,
                capability="python.analyze",
                input={"source": "value = 1"},
            )

    def test_v3_adapter_rejects_wrong_owner(self) -> None:
        runtime, tmp = self.make_runtime()
        self.addCleanup(tmp.cleanup)
        request = FriendRequest(
            owner_id="other-owner",
            text="analyze python",
            requested_tools=("python",),
        )

        with self.assertRaisesRegex(PermissionError, "Owner Special request"):
            runtime.execute_v3(
                request,
                capability="python.analyze",
                input={"source": "value = 1"},
            )


if __name__ == "__main__":
    unittest.main()
