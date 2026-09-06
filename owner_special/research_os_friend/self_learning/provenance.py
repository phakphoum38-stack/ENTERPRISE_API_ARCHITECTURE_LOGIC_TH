from __future__ import annotations

from dataclasses import dataclass

from .models import LearnedSkillCandidate


@dataclass(frozen=True)
class SkillProvenance:
    """Immutable provenance record for a promoted learned-skill version."""

    skill_name: str
    version: int
    parent_version: int | None
    source: str
    generated_by: str
    evidence_refs: tuple[str, ...] = ()
    evaluation_score: float = 0.0
    confidence: float = 0.0
    promoted_by: str | None = None
    rollback_target: int | None = None

    @classmethod
    def from_candidate(
        cls,
        candidate: LearnedSkillCandidate,
        *,
        source: str,
        generated_by: str,
        parent_version: int | None = None,
        evaluation_score: float = 0.0,
        promoted_by: str | None = None,
        rollback_target: int | None = None,
    ) -> "SkillProvenance":
        return cls(
            skill_name=candidate.name,
            version=candidate.version,
            parent_version=parent_version,
            source=source.strip(),
            generated_by=generated_by.strip(),
            evidence_refs=tuple(candidate.evidence),
            evaluation_score=max(0.0, min(1.0, float(evaluation_score))),
            confidence=candidate.normalized_confidence(),
            promoted_by=promoted_by.strip() if promoted_by else None,
            rollback_target=rollback_target,
        )


class SkillProvenanceLedger:
    """Append-only in-memory provenance history; it never mutates skill state."""

    def __init__(self) -> None:
        self._records: dict[str, tuple[SkillProvenance, ...]] = {}

    def record(self, provenance: SkillProvenance) -> SkillProvenance:
        records = self._records.setdefault(provenance.skill_name, ())
        if records and provenance.version <= records[-1].version:
            raise ValueError("provenance versions must increase monotonically")
        self._records[provenance.skill_name] = (*records, provenance)
        return provenance

    def history(self, skill_name: str) -> tuple[SkillProvenance, ...]:
        return self._records.get(skill_name, ())

    def latest(self, skill_name: str) -> SkillProvenance | None:
        records = self.history(skill_name)
        return records[-1] if records else None


@dataclass(frozen=True)
class SkillRollbackPlan:
    """Explicit rollback intent; planning never changes the active registry."""

    skill_name: str
    from_version: int
    target_version: int
    reason: str
    approved: bool = False


def plan_rollback(
    provenance: SkillProvenance,
    *,
    target_version: int | None = None,
    reason: str = "regression-feedback",
) -> SkillRollbackPlan:
    target = provenance.rollback_target if target_version is None else target_version
    if target is None:
        raise ValueError("rollback target is required")
    if target >= provenance.version:
        raise ValueError("rollback target must be older than active version")
    return SkillRollbackPlan(
        skill_name=provenance.skill_name,
        from_version=provenance.version,
        target_version=target,
        reason=reason.strip() or "regression-feedback",
    )
