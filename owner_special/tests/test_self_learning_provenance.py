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
        candidate = LearnedSkillCandidate("review", "repeat verified review", ("inspect", "validate"), ("ci-pass", "verified-result"), 0.95, "candidate", 2)
        provenance = SkillProvenance.from_candidate(candidate, source="verified-session", generated_by="SelfLearningEngine", parent_version=1, evaluation_score=0.91, promoted_by="PromotionGate", rollback_target=1)
        self.assertEqual(provenance.version, 2)
        self.assertEqual(provenance.parent_version, 1)
        self.assertEqual(provenance.evidence_refs, candidate.evidence)
        with self.assertRaises(AttributeError):
            provenance.version = 3

    def test_provenance_rejects_invalid_lineage_or_score(self):
        candidate = LearnedSkillCandidate("review", "repeat verified review", ("inspect",), confidence=0.9, version=2)
        with self.assertRaises(ValueError):
            SkillProvenance.from_candidate(candidate, source="session", generated_by="engine", parent_version=2)
        with self.assertRaises(ValueError):
            SkillProvenance.from_candidate(candidate, source="session", generated_by="engine", evaluation_score=1.1)
        with self.assertRaises(ValueError):
            SkillProvenance.from_candidate(candidate, source="session", generated_by="engine", rollback_target=2)

    def test_v1_cannot_have_parent(self):
        candidate = LearnedSkillCandidate("review", "repeat verified review", ("inspect",), version=1)
        with self.assertRaises(ValueError):
            SkillProvenance.from_candidate(candidate, source="session", generated_by="engine", parent_version=0)

    def test_v2_requires_immediate_parent(self):
        candidate = LearnedSkillCandidate("review", "repeat verified review", ("inspect",), version=2)
        with self.assertRaises(ValueError):
            SkillProvenance.from_candidate(candidate, source="session", generated_by="engine", parent_version=0)

    def test_ledger_is_append_only_and_exposes_latest(self):
        ledger = SkillProvenanceLedger()
        first = SkillProvenance("review", 1, None, "session", "engine")
        second = SkillProvenance("review", 2, 1, "feedback", "engine")
        ledger.record(first)
        ledger.record(second)
        self.assertEqual(tuple(item.version for item in ledger.history("review")), (1, 2))
        self.assertEqual(ledger.latest("review"), second)
        self.assertTrue(ledger.contains_version("review", 1))
        with self.assertRaises(ValueError):
            ledger.record(second)

    def test_ledger_rejects_broken_parent_lineage(self):
        ledger = SkillProvenanceLedger()
        ledger.record(SkillProvenance("review", 1, None, "session", "engine"))
        with self.assertRaises(ValueError):
            ledger.record(SkillProvenance("review", 3, 1, "feedback", "engine"))

    def test_rollback_requires_existing_target_when_ledger_is_supplied(self):
        ledger = SkillProvenanceLedger()
        first = SkillProvenance("review", 1, None, "session", "engine")
        active = SkillProvenance("review", 2, 1, "feedback", "engine", rollback_target=1)
        ledger.record(first)
        ledger.record(active)
        plan = plan_rollback(active, ledger=ledger)
        self.assertEqual(plan.target_version, 1)
        with self.assertRaises(ValueError):
            plan_rollback(active, target_version=0, ledger=ledger)

    def test_rollback_is_only_a_plan_until_approval(self):
        provenance = SkillProvenance("review", 3, 2, "feedback", "SelfLearningEngine", rollback_target=2)
        plan = plan_rollback(provenance)
        self.assertIsInstance(plan, SkillRollbackPlan)
        self.assertFalse(plan.approved)

    def test_rollback_rejects_forward_target(self):
        provenance = SkillProvenance("review", 2, 1, "feedback", "SelfLearningEngine")
        with self.assertRaises(ValueError):
            plan_rollback(provenance, target_version=2)


if __name__ == "__main__":
    unittest.main()
