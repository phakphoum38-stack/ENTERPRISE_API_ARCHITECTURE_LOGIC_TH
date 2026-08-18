from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from research_os_v3.autonomous_research import AutonomousResearchLoop
from research_os_v3.persistent_evidence import SQLiteEvidenceStore
from research_os_v3.persistent_tool_evidence import PersistentToolEvidenceSink
from research_os_v3.research_checkpoint import ResearchCheckpointStore
from research_os_v3.research_planner import ResearchPlanner
from research_os_v3.research_report import ReportFinding, ResearchReportBuilder
from research_os_v3.research_tools import ResearchToolRegistry, ToolRequest, ToolResult
from research_os_v3.tool_evidence import ToolEvidenceRecorder


class DeterministicResearchTool:
    name = "deterministic-research"
    capabilities = frozenset({"research.answer"})

    def execute(self, request: ToolRequest) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            success=True,
            output={"answer": f"answer for {request.input['question']}"},
            source_uri=f"https://research.test/{request.task_id}",
            metadata={"mode": "deterministic"},
        )


class ResearchE2ETests(unittest.TestCase):
    def test_question_to_persistent_evidence_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence_store = SQLiteEvidenceStore(root / "evidence.sqlite")
            checkpoints = ResearchCheckpointStore(root / "checkpoint.sqlite")
            registry = ResearchToolRegistry()
            registry.register(DeterministicResearchTool())
            recorder = ToolEvidenceRecorder(registry, PersistentToolEvidenceSink(evidence_store))
            plan = ResearchPlanner().plan(
                "What is Research OS?", sub_questions=["What is the runtime?"]
            )

            def handler(task):
                result = recorder.execute(
                    ToolRequest(
                        capability="research.answer",
                        input={"question": task.question},
                        task_id=task.id,
                    )
                )
                self.assertTrue(result.success)
                return (evidence_store.for_task(task.id)[0].id,)

            result = AutonomousResearchLoop(checkpoints).run(
                run_id="e2e-1",
                plan=plan,
                handlers={task.id: handler for task in plan.tasks},
            )

            self.assertEqual(result.status, "completed")
            self.assertEqual(len(result.completed), len(plan.tasks))
            self.assertEqual(len(evidence_store.all()), len(plan.tasks))

            findings = tuple(
                ReportFinding(
                    claim=f"Task {task.id} completed.",
                    evidence_ids=(evidence_store.for_task(task.id)[0].id,),
                    source_uris=(evidence_store.for_task(task.id)[0].source_uri,),
                    confidence=0.8,
                )
                for task in plan.tasks
            )
            report = ResearchReportBuilder().build(
                question=plan.question,
                findings=findings,
                conclusion="The deterministic research run completed successfully.",
            )
            markdown = report.to_markdown()
            self.assertIn("Research question", markdown)
            self.assertIn("https://research.test/", markdown)

            evidence_store.close()
            checkpoints.close()


if __name__ == "__main__":
    unittest.main()
