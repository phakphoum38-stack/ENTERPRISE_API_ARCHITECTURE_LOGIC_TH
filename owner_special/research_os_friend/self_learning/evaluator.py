from __future__ import annotations

from .models import LearnedSkillCandidate


class LearnedSkillEvaluator:
    """Conservative evidence score; no model or self-modifying code is executed here."""

    def score(self, candidate: LearnedSkillCandidate) -> float:
        evidence = min(len(candidate.evidence), 4) / 4.0
        procedure = min(len(candidate.procedure), 6) / 6.0
        return round(min(1.0, 0.6 * candidate.normalized_confidence() + 0.25 * evidence + 0.15 * procedure), 3)
