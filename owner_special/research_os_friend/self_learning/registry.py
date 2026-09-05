from __future__ import annotations

from .models import LearnedSkillCandidate


class LearnedSkillRegistry:
    """In-memory approved-skill registry; it never mutates the core SkillRegistry."""

    def __init__(self) -> None:
        self._approved: dict[str, LearnedSkillCandidate] = {}

    def promote(self, candidate: LearnedSkillCandidate) -> LearnedSkillCandidate:
        approved = LearnedSkillCandidate(
            name=candidate.name,
            goal=candidate.goal,
            procedure=candidate.procedure,
            evidence=candidate.evidence,
            confidence=candidate.normalized_confidence(),
            status="approved",
            version=candidate.version,
            metadata=dict(candidate.metadata),
        )
        self._approved[approved.name] = approved
        return approved

    def get(self, name: str) -> LearnedSkillCandidate | None:
        return self._approved.get(name)

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._approved))

    def snapshot(self) -> tuple[dict[str, object], ...]:
        return tuple(
            {
                "name": skill.name,
                "goal": skill.goal,
                "procedure": skill.procedure,
                "evidence": skill.evidence,
                "confidence": skill.confidence,
                "status": skill.status,
                "version": skill.version,
                "metadata": dict(skill.metadata),
            }
            for skill in self._approved.values()
        )
