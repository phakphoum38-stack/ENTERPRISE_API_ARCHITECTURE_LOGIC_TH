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


@dataclass(frozen=True)
class SkillLifecycleIntegrity:
    """Deterministic validation result for an immutable lifecycle snapshot."""

    valid: bool
    stage: str
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class SkillLifecycleCertificate:
    """Structural certificate; certification never authorizes promotion."""

    skill_name: str
    version: int
    stage: str


class SkillLifecycleAssembler:
    """Compose, validate, and structurally certify lifecycle evidence."""

    def start(self, candidate: LearnedSkillCandidate) -> SkillLifecycleSnapshot:
        return SkillLifecycleSnapshot(candidate=candidate)

    def attach_evaluation(self, snapshot: SkillLifecycleSnapshot, evaluation: SkillEvaluationRecord) -> SkillLifecycleSnapshot:
        if snapshot.evaluation is not None:
            raise ValueError("evaluation stage is already locked")
        if snapshot.provenance is not None or snapshot.promotion_evidence is not None or snapshot.promotion_record is not None:
            raise ValueError("evaluation cannot be changed after a downstream lifecycle stage")
        self._require_match(snapshot.candidate, evaluation.skill_name, evaluation.version)
        return SkillLifecycleSnapshot(snapshot.candidate, evaluation, snapshot.provenance, snapshot.promotion_evidence, snapshot.promotion_record)

    def attach_provenance(self, snapshot: SkillLifecycleSnapshot, provenance: SkillProvenance) -> SkillLifecycleSnapshot:
        if snapshot.provenance is not None:
            raise ValueError("provenance stage is already locked")
        if snapshot.promotion_evidence is not None or snapshot.promotion_record is not None:
            raise ValueError("provenance cannot be changed after a downstream lifecycle stage")
        self._require_match(snapshot.candidate, provenance.skill_name, provenance.version)
        if snapshot.candidate.version == 1 and provenance.parent_version is not None:
            raise ValueError("version 1 provenance cannot have a parent version")
        if snapshot.candidate.version > 1 and provenance.parent_version != snapshot.candidate.version - 1:
            raise ValueError("provenance parent version must match the candidate lineage")
        if snapshot.evaluation is not None:
            if provenance.evaluation_score != snapshot.evaluation.score:
                raise ValueError("provenance must match lifecycle evaluation score")
            if provenance.confidence != snapshot.evaluation.confidence:
                raise ValueError("provenance must match lifecycle evaluation confidence")
            if tuple(provenance.evidence_refs) != tuple(snapshot.evaluation.evidence_refs):
                raise ValueError("provenance must match lifecycle evaluation evidence")
        return SkillLifecycleSnapshot(snapshot.candidate, snapshot.evaluation, provenance, snapshot.promotion_evidence, snapshot.promotion_record)

    def attach_promotion_evidence(self, snapshot: SkillLifecycleSnapshot, *, provenance_ref: str, promotion_authority: str) -> SkillLifecycleSnapshot:
        if snapshot.promotion_evidence is not None:
            raise ValueError("promotion evidence stage is already locked")
        if snapshot.promotion_record is not None:
            raise ValueError("promotion evidence cannot be changed after a decision")
        if snapshot.evaluation is None or snapshot.provenance is None:
            raise ValueError("evaluation and provenance are required before promotion evidence")
        evidence = PromotionEvidenceBundle.build(snapshot.provenance, snapshot.evaluation, provenance_ref=provenance_ref, promotion_authority=promotion_authority)
        return SkillLifecycleSnapshot(snapshot.candidate, snapshot.evaluation, snapshot.provenance, evidence, snapshot.promotion_record)

    def attach_promotion_decision(self, snapshot: SkillLifecycleSnapshot, *, decision: str) -> SkillLifecycleSnapshot:
        if snapshot.promotion_record is not None:
            raise ValueError("promotion decision stage is already locked")
        if snapshot.promotion_evidence is None:
            raise ValueError("promotion evidence is required before recording a decision")
        record = SkillPromotionRecord(snapshot.candidate.name, snapshot.candidate.version, decision, snapshot.promotion_evidence)
        record.normalized_decision()
        return SkillLifecycleSnapshot(snapshot.candidate, snapshot.evaluation, snapshot.provenance, snapshot.promotion_evidence, record)

    @staticmethod
    def is_evaluation_ready(snapshot: SkillLifecycleSnapshot) -> bool:
        return snapshot.evaluation is not None

    @staticmethod
    def is_provenance_ready(snapshot: SkillLifecycleSnapshot) -> bool:
        return snapshot.evaluation is not None and snapshot.provenance is not None

    @staticmethod
    def is_promotion_ready(snapshot: SkillLifecycleSnapshot) -> bool:
        return snapshot.evaluation is not None and snapshot.provenance is not None and snapshot.promotion_evidence is not None

    @staticmethod
    def is_complete(snapshot: SkillLifecycleSnapshot) -> bool:
        return SkillLifecycleAssembler.is_promotion_ready(snapshot) and snapshot.promotion_record is not None

    @classmethod
    def validate(cls, snapshot: SkillLifecycleSnapshot) -> SkillLifecycleIntegrity:
        errors: list[str] = []
        candidate, evaluation, provenance = snapshot.candidate, snapshot.evaluation, snapshot.provenance
        evidence, record = snapshot.promotion_evidence, snapshot.promotion_record
        if evaluation is not None and (evaluation.skill_name, evaluation.version) != (candidate.name, candidate.version):
            errors.append("evaluation does not match candidate skill version")
        if provenance is not None:
            if (provenance.skill_name, provenance.version) != (candidate.name, candidate.version):
                errors.append("provenance does not match candidate skill version")
            if candidate.version == 1 and provenance.parent_version is not None:
                errors.append("version 1 provenance cannot have a parent version")
            if candidate.version > 1 and provenance.parent_version != candidate.version - 1:
                errors.append("provenance parent version does not match candidate lineage")
            if evaluation is not None:
                if provenance.evaluation_score != evaluation.score:
                    errors.append("provenance does not match evaluation score")
                if provenance.confidence != evaluation.confidence:
                    errors.append("provenance does not match evaluation confidence")
                if tuple(provenance.evidence_refs) != tuple(evaluation.evidence_refs):
                    errors.append("provenance does not match evaluation evidence")
        if evidence is not None:
            if evaluation is None or provenance is None:
                errors.append("promotion evidence requires evaluation and provenance")
            else:
                expected = PromotionEvidenceBundle.build(provenance, evaluation, provenance_ref=evidence.provenance_ref, promotion_authority=evidence.promotion_authority)
                if evidence != expected:
                    errors.append("promotion evidence does not match evaluation and provenance")
        if record is not None:
            if evidence is None:
                errors.append("promotion record requires promotion evidence")
            else:
                if (record.skill_name, record.version) != (candidate.name, candidate.version):
                    errors.append("promotion record does not match candidate skill version")
                if record.evidence != evidence:
                    errors.append("promotion record evidence is not immutable lifecycle evidence")
                try:
                    record.normalized_decision()
                except ValueError as exc:
                    errors.append(str(exc))
        if evidence is not None and (evaluation is None or provenance is None):
            errors.append("lifecycle stages are out of order")
        if record is not None and evidence is None:
            errors.append("lifecycle decision is out of order")
        return SkillLifecycleIntegrity(valid=not errors, stage=cls._stage(snapshot), errors=tuple(errors))

    @classmethod
    def certify(cls, snapshot: SkillLifecycleSnapshot) -> SkillLifecycleCertificate:
        integrity = cls.validate(snapshot)
        if not integrity.valid:
            raise ValueError("cannot certify invalid lifecycle: " + "; ".join(integrity.errors))
        if not cls.is_complete(snapshot):
            raise ValueError("lifecycle certificate requires a complete promotion decision stage")
        return SkillLifecycleCertificate(snapshot.candidate.name, snapshot.candidate.version, integrity.stage)

    @staticmethod
    def _stage(snapshot: SkillLifecycleSnapshot) -> str:
        if snapshot.promotion_record is not None:
            return "promotion_decision"
        if snapshot.promotion_evidence is not None:
            return "promotion_evidence"
        if snapshot.provenance is not None:
            return "provenance"
        if snapshot.evaluation is not None:
            return "evaluation"
        return "candidate"

    @staticmethod
    def _require_match(candidate: LearnedSkillCandidate, skill_name: str, version: int) -> None:
        if candidate.name != skill_name or candidate.version != version:
            raise ValueError("lifecycle stage must match the candidate skill version")
