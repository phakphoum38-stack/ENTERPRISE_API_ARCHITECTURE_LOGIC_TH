import unittest

from owner_special.research_os_friend.self_learning import LearnedSkillCandidate, SkillFeedback
from owner_special.research_os_friend.self_learning.evaluation_history import SkillEvaluationRecord
from owner_special.research_os_friend.self_learning.revision_cycle import (
    bind_revision_evaluation,
    propose_revision,
)


class SkillRevisionCycleTests(unittest.TestCase):
    def test_v1_feedback_produces_v2_proposal_and_preserves_all_evidence(self) -> None:
        current = LearnedSkillCandidate(
            name="bounded-research",
            goal="research safely",
            procedure=("observe", "evaluate"),
            evidence=("trace:v1",),
            confidence=0.9,
            version=1,
        )
        feedback = (
            SkillFeedback(
                skill_name="bounded-research",
                version=1,
                outcome="fail",
                evidence=("feedback:v1:timeout", "feedback:v1:trace"),
            ),
        )
        proposal = propose_revision(current, feedback)
        self.assertEqual(proposal.version, 2)
        self.assertEqual(proposal.parent_version, 1)
        self.assertEqual(
            proposal.feedback_refs,
            ("feedback:v1:timeout", "feedback:v1:trace"),
        )

    def test_revision_evaluation_binds_to_v2_using_parent_feedback(self) -> None:
        current = LearnedSkillCandidate(
            name="bounded-research",
            goal="research safely",
            procedure=("observe", "evaluate"),
            evidence=("trace:v1",),
            confidence=0.9,
            version=1,
        )
        proposal = propose_revision(
            current,
            (SkillFeedback("bounded-research", 1, "fail", ("feedback:v1",)),),
        )
        candidate_v2 = LearnedSkillCandidate(
            name="bounded-research",
            goal="research safely",
            procedure=("observe", "evaluate", "verify"),
            evidence=("trace:v2", "feedback:v1"),
            confidence=0.92,
            version=2,
            metadata={"parent_version": "1"},
        )
        evaluation = bind_revision_evaluation(
            candidate_v2,
            proposal,
            score=0.93,
            feedback=(SkillFeedback("bounded-research", 1, "fail", ("feedback:v1",)),),
        )
        self.assertIsInstance(evaluation, SkillEvaluationRecord)
        self.assertEqual(evaluation.version, 2)
        self.assertEqual(evaluation.feedback_outcomes, ("fail",))

    def test_revision_evaluation_rejects_feedback_from_wrong_parent_version(self) -> None:
        current = LearnedSkillCandidate(
            name="bounded-research",
            goal="research safely",
            procedure=("observe",),
            confidence=0.9,
            version=1,
        )
        proposal = propose_revision(current, ())
        candidate_v2 = LearnedSkillCandidate(
            name="bounded-research",
            goal="research safely",
            procedure=("observe", "verify"),
            confidence=0.9,
            version=2,
            metadata={"parent_version": "1"},
        )
        with self.assertRaises(ValueError):
            bind_revision_evaluation(
                candidate_v2,
                proposal,
                score=0.95,
                feedback=(SkillFeedback("bounded-research", 2, "fail"),),
            )

    def test_mismatched_feedback_is_rejected(self) -> None:
        current = LearnedSkillCandidate(
            name="bounded-research",
            goal="research safely",
            procedure=("observe",),
            confidence=0.9,
            version=1,
        )
        with self.assertRaises(ValueError):
            propose_revision(
                current,
                (SkillFeedback("other-skill", 1, "fail"),),
            )

    def test_revision_evaluation_rejects_out_of_range_score(self) -> None:
        current = LearnedSkillCandidate(
            name="bounded-research",
            goal="research safely",
            procedure=("observe",),
            confidence=0.9,
            version=1,
        )
        proposal = propose_revision(current, ())
        candidate_v2 = LearnedSkillCandidate(
            name="bounded-research",
            goal="research safely",
            procedure=("observe", "verify"),
            confidence=0.9,
            version=2,
            metadata={"parent_version": "1"},
        )
        with self.assertRaises(ValueError):
            bind_revision_evaluation(candidate_v2, proposal, score=1.1)

    def test_revision_evaluation_does_not_auto_promote(self) -> None:
        current = LearnedSkillCandidate(
            name="bounded-research",
            goal="research safely",
            procedure=("observe",),
            confidence=0.9,
            version=1,
        )
        proposal = propose_revision(current, ())
        candidate_v2 = LearnedSkillCandidate(
            name="bounded-research",
            goal="research safely",
            procedure=("observe", "verify"),
            confidence=0.9,
            version=2,
            metadata={"parent_version": "1"},
        )
        evaluation = bind_revision_evaluation(candidate_v2, proposal, score=0.95)
        self.assertEqual(evaluation.version, 2)
        self.assertEqual(evaluation.score, 0.95)


if __name__ == "__main__":
    unittest.main()
