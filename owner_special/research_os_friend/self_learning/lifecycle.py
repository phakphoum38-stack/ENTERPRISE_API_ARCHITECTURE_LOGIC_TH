from __future__ import annotations

from dataclasses import dataclass

from .evaluation_history import SkillEvaluationRecord
from .models import LearnedSkillCandidate
from .promotion_history import PromotionEvidenceBundle, SkillPromotionRecord
from .provenance import SkillProvenance


@dataclass(frozen=True)
class SkillLifecycleSnapshot:
    """Immutable assembly of evidence for one learned-skill lifecycle stage."""

    candidate: LearnedSkillCandidate
    evaluation: SkillEvaluationRecord | None = None
    provenance: SkillProvenance | None = None
    promotion_evidence: PromotionEvidenceBundle | None = None
    promotion_record: SkillPromotionRecord | None = None


class SkillLifecycleAssembler:
    """Compose lifecycle evidence without authorizing or executing promotion."""

    def start(self, candidate: LearnedSkillCandidate) -> SkillLifecycleSnapshot:
        return SkillLifecycleSnapshot(candidate=candidate)

    def attach_evaluation(
        self,
        snapshot: SkillLifecycleSnapshot,
        evaluation: SkillEvaluationRecord,
    ) -> SkillLifecycleSnapshot:
        self._require_match(snapshot.candidate, evaluation.skill_name, evaluation.version)
        return SkillLifecycleSnapshot(
            candidate=snapshot.candidate,
            evaluation=evaluation,
            provenance=snapshot.provenance,
            promotion_evidence=snapshot.promotion_evidence,
            promotion_record=snapshot.promotion_record,
        )

    def attach_provenance(
        self,
        snapshot: SkillLifecycleSnapshot,
        provenance: SkillProvenance,
    ) -> SkillLifecycleSnapshot:
        self._require_match(snapshot.candidate, provenance.skill_name, provenance.version)
        if snapshot.evaluation is not None:
            if provenance.evaluation_score != snapshot.evaluation.score:
                raise ValueError("provenance must match lifecycle evaluation score")
            if provenance.confidence != snapshot.evaluation.confidence:
                raise ValueError("provenance must match lifecycle evaluation confidence")
            if tuple(provenance.evidence_refs) != tuple(snapshot.evaluation.evidence_refs):
                raise ValueError("provenance must match lifecycle evaluation evidence")
        return SkillLifecycleSnapshot(
            candidate=snapshot.candidate,
            evaluation=snapshot.evaluation,
            provenance=provenance,
            promotion_evidence=snapshot.promotion_evidence,
            promotion_record=snapshot.promotion_record,
        )

    def attach_promotion_evidence(
        self,
        snapshot: SkillLifecycleSnapshot,
        *,
        provenance_ref: str,
        promotion_authority: str,
    ) -> SkillLifecycleSnapshot:
        if snapshot.evaluation is None or snapshot.provenance is None:
            raise ValueError("evaluation and provenance are required before promotion evidence")
        evidence = PromotionEvidenceBundle.build(
            snapshot.provenance,
            snapshot.evaluation,
            provenance_ref=provenance_ref,
            promotion_authority=promotion_authority,
        )
        return SkillLifecycleSnapshot(
            candidate=snapshot.candidate,
            evaluation=snapshot.evaluation,
            provenance=snapshot.provenance,
            promotion_evidence=evidence,
            promotion_record=snapshot.promotion_record,
        )

    def attach_promotion_decision(
        self,
        snapshot: SkillLifecycleSnapshot,
        *,
        decision: str,
    ) -> SkillLifecycleSnapshot:
        if snapshot.promotion_evidence is None:
            raise ValueError("promotion evidence is required before recording a decision")
        record = SkillPromotionRecord(
            skill_name=snapshot.candidate.name,
            version=snapshot.candidate.version,
            decision=decision,
            evidence=snapshot.promotion_evidence,
        )
        record.normalized_decision()
        return SkillLifecycleSnapshot(
            candidate=snapshot.candidate,
            evaluation=snapshot.evaluation,
            provenance=snapshot.provenance,
            promotion_evidence=snapshot.promotion_evidence,
            promotion_record=record,
        )

    @staticmethod
    def _require_match(
        candidate: LearnedSkillCandidate,
        skill_name: str,
        version: int,
    ) -> None:
        if candidate.name != skill_name or candidate.version != version:
            raise ValueError("lifecycle stage must match the candidate skill version")
