from __future__ import annotations

import unittest

from owner_special.research_os_friend.tool_health_gate import ToolHealthGate


class ToolHealthGateTests(unittest.TestCase):
    def test_complete_runtime_catalog_is_ready(self) -> None:
        snapshot = ToolHealthGate().snapshot(
            friend_tools=("echo", "summarize", "schedule.generate", "github.repository_status", "web.fetch"),
            v3_tools=("web", "github", "file", "python", "shell"),
        )
        self.assertEqual(snapshot["overall"], "READY")
        self.assertEqual(snapshot["counts"]["MISSING"], 0)

    def test_missing_tool_is_degraded(self) -> None:
        snapshot = ToolHealthGate().snapshot(friend_tools=(), v3_tools=())
        self.assertEqual(snapshot["overall"], "DEGRADED")
        self.assertGreater(snapshot["counts"]["MISSING"], 0)


if __name__ == "__main__":
    unittest.main()
