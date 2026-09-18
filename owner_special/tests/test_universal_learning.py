from __future__ import annotations

import unittest

from owner_special.research_os_friend.self_learning.universal_learning import (
    UniversalLearningBoundary,
)


class UniversalLearningBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = UniversalLearningBoundary()

    def test_all_universal_domains_are_available(self) -> None:
        expected = {
            "LANGUAGE", "MATHEMATICS", "SCIENCE", "ENGINEERING", "TECHNOLOGY",
            "ARTS", "DESIGN", "BUSINESS", "ECONOMICS", "LAW", "HUMANITIES",
            "SOCIAL_SCIENCE", "EDUCATION", "LIFE_AND_WORK", "RESEARCH",
        }
        self.assertEqual(self.root.DOMAINS, expected)

    def test_unknown_is_preserved(self) -> None:
        record = self.root.knowledge(
            kind="UNKNOWN",
            domain="LANGUAGE",
            statement="An unfamiliar language feature",
        )
        self.assertEqual(record.status, "UNKNOWN")
        self.assertEqual(len(record.knowledge_id), 64)

    def test_invalid_kind_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            self.root.knowledge(
                kind="MADE_UP",
                domain="SCIENCE",
                statement="x",
            )

    def test_invalid_domain_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            self.root.knowledge(
                kind="FACT",
                domain="MADE_UP",
                statement="x",
            )

    def test_understanding_requires_evidence(self) -> None:
        knowledge = self.root.knowledge(
            kind="FACT",
            domain="MATHEMATICS",
            statement="2 + 2 = 4",
        )
        with self.assertRaises(ValueError):
            self.root.understanding(
                knowledge_id=knowledge.knowledge_id,
                level="UNDERSTOOD",
                evidence_ids=(),
            )

    def test_understanding_is_evidence_bound(self) -> None:
        knowledge = self.root.knowledge(
            kind="FACT",
            domain="MATHEMATICS",
            statement="2 + 2 = 4",
        )
        evidence_id = "a" * 64
        record = self.root.understanding(
            knowledge_id=knowledge.knowledge_id,
            level="UNDERSTOOD",
            evidence_ids=(evidence_id,),
            limitations=("limited to integer arithmetic",),
        )
        self.assertEqual(record.evidence_ids, (evidence_id,))
        self.assertEqual(record.limitations, ("limited to integer arithmetic",))

    def test_self_model_requires_next_step_and_authority(self) -> None:
        with self.assertRaises(ValueError):
            self.root.self_model(
                known_ids=(),
                unknown_ids=(),
                conflicted_ids=(),
                active_goal="goal",
                current_state="state",
                next_step="",
                authority_scope="read-only",
            )

    def test_self_model_tracks_unknown_and_conflict(self) -> None:
        record = self.root.self_model(
            known_ids=("a" * 64,),
            unknown_ids=("b" * 64,),
            conflicted_ids=("c" * 64,),
            active_goal="learn",
            current_state="partial",
            next_step="test",
            authority_scope="read-only",
        )
        self.assertEqual(record.unknown_ids, ("b" * 64,))
        self.assertEqual(record.conflicted_ids, ("c" * 64,))
        self.assertEqual(record.authority_scope, "read-only")

    def test_question_and_decision_preserve_rationale(self) -> None:
        question = self.root.question("What remains unknown?")
        decision = self.root.decision(
            "Use bounded sampling",
            "10^1000 must not be materialized",
        )
        self.assertEqual(question.status, "UNKNOWN")
        self.assertIn("bounded sampling", decision.statement)
        self.assertIn("materialized", decision.rationale)


if __name__ == "__main__":
    unittest.main()
