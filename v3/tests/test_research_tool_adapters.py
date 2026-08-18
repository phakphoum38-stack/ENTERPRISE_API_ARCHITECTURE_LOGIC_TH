from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from research_os_v3.research_tool_adapters import (
    BuiltinResearchTools,
    ToolRequest,
)


class ResearchToolAdapterTests(unittest.TestCase):
    def test_file_read_returns_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "note.txt"
            path.write_text("research evidence", encoding="utf-8")
            result = BuiltinResearchTools().execute(
                ToolRequest("file", "read", {"path": str(path)})
            )
            self.assertTrue(result.success)
            self.assertEqual(result.data, "research evidence")
            self.assertTrue(result.source_uri.startswith("file://"))

    def test_python_analyze_is_deterministic(self) -> None:
        result = BuiltinResearchTools().execute(
            ToolRequest("python", "analyze", {"source": "import json\nvalue = 1"})
        )
        self.assertTrue(result.success)
        self.assertEqual(result.data["imports"], ["json"])

    def test_shell_is_allowlisted(self) -> None:
        tools = BuiltinResearchTools()
        denied = tools.execute(ToolRequest("shell", "run", {"command": ["rm", "-rf", "/"]}))
        self.assertFalse(denied.success)
        self.assertEqual(denied.error, "CommandNotAllowed")

    def test_unknown_tool_fails_closed(self) -> None:
        result = BuiltinResearchTools().execute(ToolRequest("network", "search", {}))
        self.assertFalse(result.success)
        self.assertEqual(result.error, "ToolNotFound")


if __name__ == "__main__":
    unittest.main()
