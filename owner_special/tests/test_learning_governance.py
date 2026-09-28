from __future__ import annotations

import unittest

from owner_special.research_os_friend.self_learning.learning_governance import (
    LearningGovernanceBoundary,
)


class LearningGovernanceBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = LearningGovernanceBoundary()

    def test_source_is_deterministic(self) -> None:
        first = self.root.source(
            source_type="document",
            reference="ref-1",
            observed_at="2026-09-18T00:00:00Z",
        )
        second = self.root.source(
            source_type="document",
            reference="ref-1",
            observed_at="2026-09-18T00:00:00Z",
        )
        self.assertEqual(first, second)

    def test_conflict_cannot_collapse_to_one_record(self) -> None:
        with self.assertRaises(ValueError):
            self.root.conflict(
                subject_id="subject",
                competing_ids=("a",),
                reason="insufficient comparison",
            )

    def test_applicable_transfer_requires_evidence(self) -> None:
        with self.assertRaises(ValueError):
            self.root.transfer(
                source_knowledge_id="knowledge",
                target_domain="BUSINESS",
                applicable=True,
                evidence_ids=(),
            )

    def test_correction_requires_reason_and_evidence(self) -> None:
        with self.assertRaises(ValueError):
            self.root.correction(
                target_id="knowledge",
                previous_state="KNOWN",
                corrected_state="UNKNOWN",
                reason="",
                evidence_ids=("a" * 64,),
            )

    def test_recovery_preserves_next_step(self) -> None:
        record = self.root.recovery(
            goal="finish task",
            current_state="partial",
            completed=("step-1",),
            pending=("step-2",),
            blocked=(),
            evidence_ids=("a" * 64,),
            next_step="step-2",
        )
        self.assertEqual(record.pending, ("step-2",))
        self.assertEqual(record.next_step, "step-2")


if __name__ == "__main__":
    unittest.main()
