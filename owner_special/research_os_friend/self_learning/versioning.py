from __future__ import annotations

from dataclasses import dataclass

from .models import LearnedSkillCandidate


@dataclass(frozen=True)
class SkillVersionProposal:
    """Immutable proposal linking a new learned skill version to its parent."""

    skill_name: str
    version: int
    parent_version: int | None
    change_reason: str


def propose_next_version(
    candidate: LearnedSkillCandidate,
    existing: LearnedSkillCandidate | None,
    *,
    change_reason: str = "new-learning-result",
) -> SkillVersionProposal:
    """Calculate the next version without mutating any registered skill."""
    parent_version = existing.version if existing is not None else None
    next_version = (parent_version + 1) if parent_version is not None else max(1, candidate.version)
    return SkillVersionProposal(
        skill_name=candidate.name,
        version=next_version,
        parent_version=parent_version,
        change_reason=change_reason.strip() or "new-learning-result",
    )
