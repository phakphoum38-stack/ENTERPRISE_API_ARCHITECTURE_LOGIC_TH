from __future__ import annotations

from .models import LearnedSkillCandidate


class LearnedSkillValidator:
    """Deterministic safety/quality checks before promotion."""

    MAX_STEPS = 12
    MIN_CONFIDENCE = 0.75

    def validate(self, candidate: LearnedSkillCandidate) -> tuple[bool, tuple[str, ...]]:
        reasons: list[str] = []
        if not candidate.name.strip():
            reasons.append("empty-name")
        if not candidate.goal.strip():
            reasons.append("empty-goal")
        if not candidate.procedure or len(candidate.procedure) > self.MAX_STEPS:
            reasons.append("invalid-procedure-length")
        if any(not step.strip() for step in candidate.procedure):
            reasons.append("empty-procedure-step")
        if candidate.normalized_confidence() < self.MIN_CONFIDENCE:
            reasons.append("low-confidence")
        if any(token in " ".join(candidate.procedure).lower() for token in ("secret", "password", "api key", "credential")):
            reasons.append("secret-handling-in-procedure")
        return not reasons, tuple(reasons)
