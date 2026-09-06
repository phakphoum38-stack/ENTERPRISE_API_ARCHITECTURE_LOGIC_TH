import unittest

from owner_special.research_os_friend.self_learning import (
    LearnedSkillCandidate,
    SkillProvenance,
    SkillRollbackPlan,
    plan_rollback,
)


class SelfLearningProvenanceTests(unittest.TestCase):
    def test_provenance_is_immutable_and_binds_candidate_evidence(self):
        candidate = LearnedSkillCandidate(
            name="review",
            goal="repeat verified review",
            procedure=("inspect", "validate"),
            evidence=("ci-pass", "verified-result"),
            confidence=0.95,
            version=2,
        )
        provenance = SkillProvenance.from_candidate(
            candidate,
            source="verified-session",
            generated_by="SelfLearningEngine",
            parent_version=1,
            evaluation_score=0.91,
            promoted_by="PromotionGate",
            rollback_target=1,
        )
        self.assertEqual(provenance.version, 2)
        self.assertEqual(provenance.parent_version, 1)
        self.assertEqual(provenance.evidence_refs, candidate.evidence)
        with self.assertRaises(AttributeError):
            provenance.version = 3

    def test_rollback_is_only_a_plan_until_approval(self):
        provenance = SkillProvenance(
            skill_name="review",
            version=3,
            parent_version=2,
            source="feedback",
            generated_by="SelfLearningEngine",
            rollback_target=2,
        )
        plan = plan_rollback(provenance)
        self.assertIsInstance(plan, SkillRollbackPlan)
        self.assertEqual(plan.from_version, 3)
        self.assertEqual(plan.target_version, 2)
        self.assertFalse(plan.approved)

    def test_rollback_rejects_forward_target(self):
        provenance = SkillProvenance(
            skill_name="review",
            version=2,
            parent_version=1,
            source="feedback",
            generated_by="SelfLearningEngine",
        )
        with self.assertRaises(ValueError):
            plan_rollback(provenance, target_version=2)


if __name__ == "__main__":
    unittest.main()
