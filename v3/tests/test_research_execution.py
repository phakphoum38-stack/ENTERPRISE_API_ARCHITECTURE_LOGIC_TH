from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from research_os_v3.evidence import Evidence
from research_os_v3.persistent_evidence import SQLiteEvidenceStore
from research_os_v3.queue import DurableTaskQueue
from research_os_v3.research_execution import ResearchExecutionCoordinator
from research_os_v3.research_planner import ResearchPlanner


class ResearchExecutionTests(unittest.TestCase):
    def test_dag_executes_in_dependency_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            queue = DurableTaskQueue(Path(tmp) / "queue.sqlite")
            plan = ResearchPlanner().plan(
                "How does research execution work?",
                sub_questions=("How is work queued?", "How does the runner execute?"),
            )
            order: list[str] = []

            def handler(task, _item):
                order.append(task.kind.value)

            handlers = {task.id: handler for task in plan.tasks}
            result = ResearchExecutionCoordinator(queue).run(plan, handlers)

            self.assertEqual(len(result.completed), 5)
            self.assertEqual(result.failed, ())
            self.assertEqual(order[0], "discover")
            self.assertEqual(order[-2:], ["analyze", "synthesize"])
            queue.close()

    def test_missing_handler_is_retried_then_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            queue = DurableTaskQueue(Path(tmp) / "queue.sqlite")
            plan = ResearchPlanner().plan("What happens without a handler?")
            result = ResearchExecutionCoordinator(queue, max_attempts=2).run(plan, {})
            self.assertEqual(result.completed, ())
            self.assertEqual(result.failed, (plan.tasks[0].id,))
            self.assertEqual(len(result.retried), 1)
            queue.close()

    def test_evidence_survives_store_reopen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "evidence.db"
            item = Evidence(
                id="e1", claim="queue is durable", source_uri="https://example.test",
                task_id="t1", confidence=0.9,
            )
            store = SQLiteEvidenceStore(path)
            store.add(item)
            store.close()
            reopened = SQLiteEvidenceStore(path)
            self.assertEqual(reopened.get("e1"), item)
            reopened.close()


if __name__ == "__main__":
    unittest.main()
