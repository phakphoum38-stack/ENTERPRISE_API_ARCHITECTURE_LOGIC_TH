from __future__ import annotations

from .models import LearnedSkillCandidate
from .promotion_gate import SkillPromotionGate
from .registry import LearnedSkillRegistry


class SelfLearningEngine:
    """Bounded learning loop: observe -> propose -> validate -> score -> promote."""

    MAX_STEPS = 6

    def __init__(self, registry: LearnedSkillRegistry | None = None, gate: SkillPromotionGate | None = None) -> None:
        self.registry = registry or LearnedSkillRegistry()
        self.gate = gate or SkillPromotionGate()

    def propose(
        self,
        *,
        name: str,
        goal: str,
        procedure: tuple[str, ...],
        evidence: tuple[str, ...] = (),
        confidence: float = 0.0,
    ) -> LearnedSkillCandidate:
        if len(procedure) > self.MAX_STEPS:
            raise ValueError(f"learning procedure exceeds {self.MAX_STEPS} steps")
        return LearnedSkillCandidate(
            name=name,
            goal=goal,
            procedure=procedure,
            evidence=evidence,
            confidence=confidence,
        )

    def learn(self, candidate: LearnedSkillCandidate) -> LearnedSkillCandidate | None:
        """Promote only validated candidates; core skills remain untouched."""
        return self.gate.promote(candidate, self.registry)

    def snapshot(self) -> dict[str, object]:
        return {
            "mode": "bounded",
            "core_mutation": False,
            "approval_required": True,
            "approved_skills": self.registry.snapshot(),
        }
