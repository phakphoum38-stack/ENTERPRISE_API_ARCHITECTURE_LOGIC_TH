from __future__ import annotations

from .models import LearnedSkillCandidate


class LearnedSkillValidator:
    """Deterministic safety/quality checks before promotion."""

    MAX_STEPS = 12
    MAX_EVIDENCE = 16
    MAX_EVIDENCE_LENGTH = 512
    MIN_CONFIDENCE = 0.75

    def validate(self, candidate: LearnedSkillCandidate) -> tuple[bool, tuple[str, ...]]:
        reasons: list[str] = []
        if not candidate.name.strip():
            reasons.append("empty-name")
        if not candidate.goal.strip():
            reasons.append("empty-goal")
        if not candidate.procedure or len(candidate.procedure) > self.MAX_STEPS:
            reasons.append("invalid-procedure-length")
        if any(not isinstance(step, str) or not step.strip() for step in candidate.procedure):
            reasons.append("empty-procedure-step")
        if not candidate.evidence:
            reasons.append("missing-evidence")
        elif len(candidate.evidence) > self.MAX_EVIDENCE:
            reasons.append("too-many-evidence-references")
        else:
            for evidence in candidate.evidence:
                if not isinstance(evidence, str) or not evidence.strip():
                    reasons.append("invalid-evidence-reference")
                    break
                if len(evidence) > self.MAX_EVIDENCE_LENGTH:
                    reasons.append("oversized-evidence-reference")
                    break
        if candidate.normalized_confidence() < self.MIN_CONFIDENCE:
            reasons.append("low-confidence")
        procedure_text = " ".join(candidate.procedure).lower()
        evidence_text = " ".join(str(item) for item in candidate.evidence).lower()
        unsafe_terms = ("secret", "password", "api key", "credential", "private key", "bearer ")
        if any(token in procedure_text for token in unsafe_terms):
            reasons.append("secret-handling-in-procedure")
        if any(token in evidence_text for token in unsafe_terms):
            reasons.append("secret-handling-in-evidence")
        return not reasons, tuple(reasons)
