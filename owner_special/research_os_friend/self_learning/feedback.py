from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SkillFeedback:
    """Owner-scoped feedback used as evidence for future evaluation."""

    skill_name: str
    version: int
    outcome: str
    evidence: tuple[str, ...] = ()
    notes: str = ""

    def normalized_outcome(self) -> str:
        return self.outcome.strip().lower()

    def is_positive(self) -> bool:
        return self.normalized_outcome() in {"pass", "passed", "success", "successful", "approved"}

    def is_negative(self) -> bool:
        return self.normalized_outcome() in {"fail", "failed", "error", "rejected"}
