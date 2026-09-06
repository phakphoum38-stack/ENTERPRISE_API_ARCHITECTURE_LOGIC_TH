import unittest

from owner_special.research_os_friend.self_learning import (
    LearnedSkillCandidate,
    SkillEvaluationRecord,
    SkillPromotionLedger,
    SkillPromotionRecord,
    SkillProvenance,
    PromotionEvidenceBundle,
)


class SkillPromotionHistoryTests(unittest.TestCase):
    def _evidence(self) -> tuple[SkillProvenance, SkillEvaluationRecord]:
        candidate = LearnedSkillCandidate(
            name="bounded-research",
            goal="research safely",
            procedure=("observe", "evaluate"),
            evidence=("trace:42", "eval:42"),
            confidence=0.9,
            version=2,
        )
        evaluation = SkillEvaluationRecord.from_candidate(candidate, score=0.9)
        provenance = SkillProvenance.from_candidate(
            candidate,
            source="owner-feedback",
            generated_by="self-learning-v2",
            parent_version=1,
            evaluation_score=0.9,
            promoted_by="OwnerPolicy",
        )
        return provenance, evaluation

    def test_build_binds_provenance_and_evaluation_exactly(self) -> None:
        provenance, evaluation = self._evidence()
        bundle = PromotionEvidenceBundle.build(
            provenance,
            evaluation,
            provenance_ref="prov:bounded-research:v2",
            promotion_authority="OwnerPolicy",
        )
        self.assertEqual(bundle.version, 2)
        self.assertEqual(bundle.evidence_refs, ("trace:42", "eval:42"))
        self.assertEqual(bundle.promotion_authority, "OwnerPolicy")

    def test_mismatched_evaluation_cannot_be_attached(self) -> None:
        provenance, evaluation = self._evidence()
        wrong = SkillEvaluationRecord(
            skill_name=evaluation.skill_name,
            version=1,
            score=evaluation.score,
            confidence=evaluation.confidence,
            evidence_refs=evaluation.evidence_refs,
        )
        with self.assertRaises(ValueError):
            PromotionEvidenceBundle.build(
                provenance,
                wrong,
                provenance_ref="prov:bounded-research:v2",
                promotion_authority="OwnerPolicy",
            )

    def test_ledger_is_append_only_and_version_bound(self) -> None:
        provenance, evaluation = self._evidence()
        bundle = PromotionEvidenceBundle.build(
            provenance,
            evaluation,
            provenance_ref="prov:bounded-research:v2",
            promotion_authority="OwnerPolicy",
        )
        record = SkillPromotionRecord(
            skill_name="bounded-research",
            version=2,
            decision="approved",
            evidence=bundle,
        )
        ledger = SkillPromotionLedger()
        self.assertIs(ledger.record(record), record)
        self.assertIs(ledger.record(record), record)
        self.assertEqual(ledger.latest_approved("bounded-research"), record)

        conflicting = SkillPromotionRecord(
            skill_name="bounded-research",
            version=2,
            decision="rejected",
            evidence=bundle,
        )
        with self.assertRaises(ValueError):
            ledger.record(conflicting)

    def test_ledger_rejects_backward_versions(self) -> None:
        provenance, evaluation = self._evidence()
        bundle = PromotionEvidenceBundle.build(
            provenance,
            evaluation,
            provenance_ref="prov:bounded-research:v2",
            promotion_authority="OwnerPolicy",
        )
        ledger = SkillPromotionLedger()
        ledger.record(
            SkillPromotionRecord("bounded-research", 2, "approved", bundle)
        )
        with self.assertRaises(ValueError):
            ledger.record(
                SkillPromotionRecord("bounded-research", 1, "approved", bundle)
            )


if __name__ == "__main__":
    unittest.main()
