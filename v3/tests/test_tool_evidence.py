from __future__ import annotations

import unittest

from research_os_v3.research_tools import ResearchToolRegistry, ToolRequest, ToolResult
from research_os_v3.tool_evidence import InMemoryEvidenceSink, ToolEvidenceRecorder


class FakeTool:
    name = "fake-search"
    capabilities = frozenset({"search"})

    def execute(self, request: ToolRequest) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            success=True,
            output={"answer": "ok"},
            source_uri="https://example.test/source",
            metadata={"kind": "test"},
        )


class ToolEvidenceTests(unittest.TestCase):
    def test_successful_tool_call_becomes_evidence(self) -> None:
        registry = ResearchToolRegistry()
        registry.register(FakeTool())
        sink = InMemoryEvidenceSink()
        result = ToolEvidenceRecorder(registry, sink).execute(
            ToolRequest("search", {"query": "x"}, task_id="task-1")
        )
        self.assertTrue(result.success)
        self.assertEqual(len(sink.items), 1)
        evidence = sink.items[0]
        self.assertEqual(evidence.task_id, "task-1")
        self.assertEqual(evidence.source_uri, "https://example.test/source")
        self.assertTrue(evidence.evidence_id.startswith("tool-"))

    def test_failed_tool_call_creates_no_evidence(self) -> None:
        class FailingTool:
            name = "failing"
            capabilities = frozenset({"search"})

            def execute(self, request):
                return ToolResult(tool_name=self.name, success=False, error="failed")

        registry = ResearchToolRegistry()
        registry.register(FailingTool())
        sink = InMemoryEvidenceSink()
        ToolEvidenceRecorder(registry, sink).execute(ToolRequest("search", {}, task_id="task-2"))
        self.assertEqual(sink.items, [])


if __name__ == "__main__":
    unittest.main()
