from __future__ import annotations

import unittest

from research_os_v3.research_report import ReportFinding, ResearchReportBuilder
from research_os_v3.research_tools import ResearchToolRegistry, ToolRequest, ToolResult


class FakeTool:
    name = "fake.search"
    capabilities = frozenset({"search"})

    def execute(self, request: ToolRequest) -> ToolResult:
        return ToolResult(self.name, True, {"q": request.input["q"]}, "https://example.test/source")


class ResearchToolsAndReportTests(unittest.TestCase):
    def test_registry_resolves_and_executes_capability(self) -> None:
        registry = ResearchToolRegistry()
        registry.register(FakeTool())
        result = registry.execute(ToolRequest("search", {"q": "research"}))
        self.assertTrue(result.success)
        self.assertEqual(result.tool_name, "fake.search")
        self.assertEqual(registry.names(), ("fake.search",))

    def test_report_contains_citations(self) -> None:
        report = ResearchReportBuilder().build(
            question="What is X?",
            findings=(ReportFinding("X exists", ("e1",), ("https://example.test/x",), 0.9),),
            conclusion="X exists based on the collected evidence.",
        )
        markdown = report.to_markdown()
        self.assertIn("[1](https://example.test/x)", markdown)
        self.assertIn("confidence=0.90", markdown)


if __name__ == "__main__":
    unittest.main()
