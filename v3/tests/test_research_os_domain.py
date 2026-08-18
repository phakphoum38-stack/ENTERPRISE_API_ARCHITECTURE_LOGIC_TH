from __future__ import annotations

import unittest

from research_os_v3.brain import BrainCore
from research_os_v3.evidence import Evidence, EvidenceStore, evidence_id
from research_os_v3.research_planner import ResearchPlanError, ResearchPlanner, ready_tasks
from research_os_v3.synthesis import ResearchSynthesizer


class ResearchOSDomainTests(unittest.TestCase):
    def test_brain_creates_dependency_safe_plan(self) -> None:
        plan = BrainCore().create_research_plan(
            "How does the system scale?",
            sub_questions=("What is the queue model?", "How are runners isolated?"),
        )
        self.assertEqual(len(plan.tasks), 5)
        self.assertEqual(len(ready_tasks(plan, set())), 1)

        completed = {plan.tasks[0].id}
        ready = ready_tasks(plan, completed)
        self.assertEqual(len(ready), 2)

    def test_empty_question_is_rejected(self) -> None:
        with self.assertRaises(ResearchPlanError):
            ResearchPlanner().plan("   ")

    def test_evidence_identity_is_stable(self) -> None:
        self.assertEqual(
            evidence_id("A claim", "https://example.test", "excerpt"),
            evidence_id("A claim", "https://example.test", "excerpt"),
        )

    def test_evidence_requires_source_and_is_queryable(self) -> None:
        store = EvidenceStore()
        item = Evidence(
            id="e1",
            claim="The queue is durable.",
            source_uri="https://example.test/source",
            task_id="task-1",
            confidence=0.9,
        )
        store.add(item)
        self.assertEqual(store.for_task("task-1"), (item,))

    def test_synthesis_preserves_provenance(self) -> None:
        items = [
            Evidence(
                id="e1",
                claim="The queue is durable.",
                source_uri="https://example.test/a",
                confidence=0.8,
            ),
            Evidence(
                id="e2",
                claim="The queue is durable.",
                source_uri="https://example.test/b",
                confidence=0.9,
            ),
        ]
        result = ResearchSynthesizer().synthesize("Queue durability", items)
        self.assertEqual(len(result.findings), 1)
        self.assertEqual(result.findings[0].evidence_ids, ("e1", "e2"))
        self.assertEqual(result.findings[0].confidence, 0.9)
        self.assertFalse(result.conflicts)


if __name__ == "__main__":
    unittest.main()
