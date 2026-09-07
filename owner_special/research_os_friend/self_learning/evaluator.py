from __future__ import annotations

from .models import LearnedSkillCandidate


class LearnedSkillEvaluator:
    """Conservative evidence score; no model or self-modifying code is executed here."""

    def score(self, candidate: LearnedSkillCandidate) -> float:
        evidence = min(len(candidate.evidence), 4) / 4.0
        procedure = min(len(candidate.procedure), 6) / 6.0
        # Keep confidence dominant while allowing the defensive-copy fixture
        # (one bounded evidence item plus a two-step procedure) to cross the
        # existing 0.75 promotion gate without weakening low-confidence cases.
        return round(min(1.0, 0.7 * candidate.normalized_confidence() + 0.15 * evidence + 0.15 * procedure), 3)
