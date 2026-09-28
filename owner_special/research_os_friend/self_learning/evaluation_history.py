from __future__ import annotations

from dataclasses import dataclass

from .feedback import SkillFeedback
from .models import LearnedSkillCandidate


@dataclass(frozen=True)
class SkillEvaluationRecord:
    """Immutable evaluation result bound to one skill version."""

    skill_name: str
    version: int
    score: float
    confidence: float
    evidence_refs: tuple[str, ...] = ()
    feedback_outcomes: tuple[str, ...] = ()

    @classmethod
    def from_candidate(
        cls,
        candidate: LearnedSkillCandidate,
        *,
        score: float,
        feedback: tuple[SkillFeedback, ...] = (),
    ) -> "SkillEvaluationRecord":
        if score < 0.0 or score > 1.0:
            raise ValueError("evaluation score must be between 0 and 1")
        for item in feedback:
            if item.skill_name != candidate.name or item.version != candidate.version:
                raise ValueError("feedback must match evaluated skill version")
        return cls(
            skill_name=candidate.name,
            version=candidate.version,
            score=round(float(score), 3),
            confidence=candidate.normalized_confidence(),
            evidence_refs=tuple(candidate.evidence),
            feedback_outcomes=tuple(item.normalized_outcome() for item in feedback),
        )


class SkillEvaluationLedger:
    """Append-only evaluation history; records evidence but never promotes skills."""

    def __init__(self) -> None:
        self._records: dict[str, tuple[SkillEvaluationRecord, ...]] = {}

    def record(self, record: SkillEvaluationRecord) -> SkillEvaluationRecord:
        records = self._records.setdefault(record.skill_name, ())
        if records and record.version < records[-1].version:
            raise ValueError("evaluation versions cannot move backwards")
        if records and record.version == records[-1].version and record != records[-1]:
            raise ValueError("evaluation record for a version is immutable")
        self._records[record.skill_name] = (*records, record) if not records or records[-1] != record else records
        return record

    def history(self, skill_name: str) -> tuple[SkillEvaluationRecord, ...]:
        return self._records.get(skill_name, ())

    def latest(self, skill_name: str) -> SkillEvaluationRecord | None:
        records = self.history(skill_name)
        return records[-1] if records else None


def aggregate_feedback(feedback: tuple[SkillFeedback, ...]) -> tuple[int, int, float]:
    """Summarize feedback without turning it into an authorization decision."""
    positive = sum(item.is_positive() for item in feedback)
    negative = sum(item.is_negative() for item in feedback)
    total = positive + negative
    rate = round(positive / total, 3) if total else 0.0
    return positive, negative, rate
