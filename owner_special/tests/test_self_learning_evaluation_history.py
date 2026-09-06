import unittest

from owner_special.research_os_friend.self_learning import (
    LearnedSkillCandidate,
    SkillEvaluationLedger,
    SkillEvaluationRecord,
    SkillFeedback,
    aggregate_feedback,
)


class SelfLearningEvaluationHistoryTests(unittest.TestCase):
    def test_evaluation_binds_feedback_to_exact_version(self):
        candidate = LearnedSkillCandidate(
            name="review",
            goal="repeat verified review",
            procedure=("inspect", "validate"),
            evidence=("ci-pass",),
            confidence=0.9,
            version=2,
        )
        feedback = SkillFeedback(
            skill_name="review",
            version=2,
            outcome="passed",
            evidence=("verified",),
        )
        record = SkillEvaluationRecord.from_candidate(
            candidate,
            score=0.88,
            feedback=(feedback,),
        )
        self.assertEqual(record.version, 2)
        self.assertEqual(record.feedback_outcomes, ("passed",))
        self.assertEqual(record.evidence_refs, ("ci-pass",))

    def test_evaluation_ledger_is_append_only_and_versioned(self):
        ledger = SkillEvaluationLedger()
        first = SkillEvaluationRecord("review", 1, 0.8, 0.8, ("a",))
        second = SkillEvaluationRecord("review", 2, 0.9, 0.9, ("b",))
        ledger.record(first)
        ledger.record(second)
        self.assertEqual(ledger.history("review"), (first, second))
        self.assertEqual(ledger.latest("review"), second)
        with self.assertRaises(ValueError):
            ledger.record(SkillEvaluationRecord("review", 1, 0.7, 0.7, ("changed",)))

    def test_feedback_aggregation_is_observational_only(self):
        feedback = (
            SkillFeedback("review", 2, "passed"),
            SkillFeedback("review", 2, "failed"),
            SkillFeedback("review", 2, "success"),
            SkillFeedback("review", 2, "unknown"),
        )
        self.assertEqual(aggregate_feedback(feedback), (2, 1, 0.667))

    def test_feedback_version_mismatch_is_rejected(self):
        candidate = LearnedSkillCandidate(
            name="review",
            goal="repeat verified review",
            procedure=("inspect",),
            confidence=0.9,
            version=2,
        )
        feedback = SkillFeedback("review", 1, "passed")
        with self.assertRaises(ValueError):
            SkillEvaluationRecord.from_candidate(candidate, score=0.9, feedback=(feedback,))


if __name__ == "__main__":
    unittest.main()
