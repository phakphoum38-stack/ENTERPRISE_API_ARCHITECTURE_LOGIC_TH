from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from research_os_v3.autonomous_research import AutonomousResearchLoop
from research_os_v3.research_checkpoint import ResearchCheckpointStore
from research_os_v3.research_planner import ResearchPlanner


class AutonomousResearchTests(unittest.TestCase):
    def test_loop_completes_and_persists_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ResearchCheckpointStore(Path(tmp) / "research.sqlite")
            plan = ResearchPlanner().plan("Explain X", sub_questions=["What is X?"])
            calls: list[str] = []

            def handler(task):
                calls.append(task.id)
                return (f"evidence:{task.id}",)

            result = AutonomousResearchLoop(store).run(
                run_id="run-1", plan=plan, handlers={task.id: handler for task in plan.tasks}
            )
            self.assertEqual(result.status, "completed")
            self.assertEqual(set(result.completed), set(plan.task_ids()))
            self.assertEqual(len(result.evidence_ids), len(plan.tasks))
            self.assertGreaterEqual(len(calls), 4)
            store.close()

    def test_loop_resumes_from_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "research.sqlite"
            store = ResearchCheckpointStore(path)
            plan = ResearchPlanner().plan("Explain X")
            first_task = plan.tasks[0]
            store.save(__import__("research_os_v3.research_checkpoint", fromlist=["ResearchCheckpoint"]).ResearchCheckpoint(
                run_id="run-2", plan_question=plan.question, completed_tasks=(first_task.id,)
            ))
            calls: list[str] = []
            result = AutonomousResearchLoop(store).run(
                run_id="run-2", plan=plan,
                handlers={task.id: lambda task: calls.append(task.id) or (task.id, ) for task in plan.tasks},
            )
            self.assertEqual(result.status, "completed")
            self.assertNotIn(first_task.id, calls)
            store.close()


if __name__ == "__main__":
    unittest.main()
