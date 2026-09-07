from __future__ import annotations

from .models import LearnedSkillCandidate


class LearnedSkillEvaluator:
    """Conservative evidence score; no model or self-modifying code is executed here."""

    def score(self, candidate: LearnedSkillCandidate) -> float:
        evidence = min(len(candidate.evidence), 4) / 4.0
        procedure = min(len(candidate.procedure), 6) / 6.0
        # Keep confidence dominant while allowing a well-supported, bounded
        # candidate to cross the existing 0.75 promotion gate.
        return round(min(1.0, 0.65 * candidate.normalized_confidence() + 0.2 * evidence + 0.15 * procedure), 3)
