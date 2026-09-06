from __future__ import annotations

from .evaluator import LearnedSkillEvaluator
from .models import LearnedSkillCandidate
from .registry import LearnedSkillRegistry
from .validator import LearnedSkillValidator


class SkillPromotionGate:
    """Require validation and evidence before a candidate becomes reusable."""

    def __init__(self, *, validator: LearnedSkillValidator | None = None, evaluator: LearnedSkillEvaluator | None = None) -> None:
        self.validator = validator or LearnedSkillValidator()
        self.evaluator = evaluator or LearnedSkillEvaluator()

    def promote(self, candidate: LearnedSkillCandidate, registry: LearnedSkillRegistry) -> LearnedSkillCandidate | None:
        valid, _ = self.validator.validate(candidate)
        score = self.evaluator.score(candidate)
        if not valid or score < LearnedSkillValidator.MIN_CONFIDENCE:
            return None
        return registry.promote(candidate)
