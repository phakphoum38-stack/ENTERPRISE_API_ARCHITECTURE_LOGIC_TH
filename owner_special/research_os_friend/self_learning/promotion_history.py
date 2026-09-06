from __future__ import annotations

from dataclasses import dataclass

from .evaluation_history import SkillEvaluationRecord
from .provenance import SkillProvenance


@dataclass(frozen=True)
class PromotionEvidenceBundle:
    """Immutable evidence package describing one promotion decision."""

    skill_name: str
    version: int
    provenance_ref: str
    evidence_refs: tuple[str, ...]
    evaluation_score: float
    confidence: float
    promotion_authority: str

    @classmethod
    def build(
        cls,
        provenance: SkillProvenance,
        evaluation: SkillEvaluationRecord,
        *,
        provenance_ref: str,
        promotion_authority: str,
    ) -> "PromotionEvidenceBundle":
        if provenance.skill_name != evaluation.skill_name or provenance.version != evaluation.version:
            raise ValueError("provenance and evaluation must match the promoted skill version")
        if provenance.evaluation_score != evaluation.score:
            raise ValueError("provenance and evaluation scores must match")
        if provenance.confidence != evaluation.confidence:
            raise ValueError("provenance and evaluation confidence must match")
        if tuple(provenance.evidence_refs) != tuple(evaluation.evidence_refs):
            raise ValueError("provenance and evaluation evidence must match")
        if not provenance_ref.strip():
            raise ValueError("provenance reference is required")
        if not promotion_authority.strip():
            raise ValueError("promotion authority is required")
        return cls(
            skill_name=provenance.skill_name,
            version=provenance.version,
            provenance_ref=provenance_ref.strip(),
            evidence_refs=tuple(evaluation.evidence_refs),
            evaluation_score=evaluation.score,
            confidence=evaluation.confidence,
            promotion_authority=promotion_authority.strip(),
        )


@dataclass(frozen=True)
class SkillPromotionRecord:
    """Immutable, inspectable history entry; recording is not authorization."""

    skill_name: str
    version: int
    decision: str
    evidence: PromotionEvidenceBundle

    def normalized_decision(self) -> str:
        decision = self.decision.strip().lower()
        if decision not in {"approved", "rejected"}:
            raise ValueError("promotion decision must be approved or rejected")
        return decision


class SkillPromotionLedger:
    """Append-only promotion history with immutable per-version decisions."""

    def __init__(self) -> None:
        self._records: dict[str, tuple[SkillPromotionRecord, ...]] = {}

    def record(self, record: SkillPromotionRecord) -> SkillPromotionRecord:
        records = self._records.setdefault(record.skill_name, ())
        if record.evidence.skill_name != record.skill_name or record.evidence.version != record.version:
            raise ValueError("promotion evidence must match the promotion record")
        normalized_decision = record.normalized_decision()
        if records and record.version < records[-1].version:
            raise ValueError("promotion versions cannot move backwards")
        if records and record.version == records[-1].version and record != records[-1]:
            raise ValueError("promotion record for a version is immutable")
        if records and record.version == records[-1].version:
            return records[-1]
        if normalized_decision == "approved" and record.evidence.evaluation_score < 0.75:
            raise ValueError("approved promotion requires minimum evaluation confidence")
        self._records[record.skill_name] = (*records, record)
        return record

    def history(self, skill_name: str) -> tuple[SkillPromotionRecord, ...]:
        return self._records.get(skill_name, ())

    def latest(self, skill_name: str) -> SkillPromotionRecord | None:
        records = self.history(skill_name)
        return records[-1] if records else None

    def latest_approved(self, skill_name: str) -> SkillPromotionRecord | None:
        for record in reversed(self.history(skill_name)):
            if record.normalized_decision() == "approved":
                return record
        return None
