import unittest

from owner_special.research_os_friend.self_learning import (
    LearnedSkillCandidate,
    SkillProvenance,
    SkillProvenanceLedger,
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

    def test_provenance_rejects_invalid_lineage_or_score(self):
        candidate = LearnedSkillCandidate(
            name="review",
            goal="repeat verified review",
            procedure=("inspect",),
            confidence=0.9,
            version=2,
        )
        with self.assertRaises(ValueError):
            SkillProvenance.from_candidate(
                candidate,
                source="session",
                generated_by="engine",
                parent_version=2,
            )
        with self.assertRaises(ValueError):
            SkillProvenance.from_candidate(
                candidate,
                source="session",
                generated_by="engine",
                evaluation_score=1.1,
            )
        with self.assertRaises(ValueError):
            SkillProvenance.from_candidate(
                candidate,
                source="session",
                generated_by="engine",
                rollback_target=2,
            )

    def test_ledger_is_append_only_and_exposes_latest(self):
        ledger = SkillProvenanceLedger()
        first = SkillProvenance("review", 1, None, "session", "engine")
        second = SkillProvenance("review", 2, 1, "feedback", "engine")
        ledger.record(first)
        ledger.record(second)
        self.assertEqual(tuple(item.version for item in ledger.history("review")), (1, 2))
        self.assertEqual(ledger.latest("review"), second)
        with self.assertRaises(ValueError):
            ledger.record(second)

    def test_ledger_rejects_broken_parent_lineage(self):
        ledger = SkillProvenanceLedger()
        ledger.record(SkillProvenance("review", 1, None, "session", "engine"))
        with self.assertRaises(ValueError):
            ledger.record(SkillProvenance("review", 3, 1, "feedback", "engine"))

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
