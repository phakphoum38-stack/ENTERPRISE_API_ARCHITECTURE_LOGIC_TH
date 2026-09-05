from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LearnedSkillCandidate:
    """A proposed skill; candidates are data until explicitly promoted."""

    name: str
    goal: str
    procedure: tuple[str, ...]
    evidence: tuple[str, ...] = ()
    confidence: float = 0.0
    status: str = "candidate"
    version: int = 1
    metadata: dict[str, str] = field(default_factory=dict)

    def normalized_confidence(self) -> float:
        return max(0.0, min(1.0, float(self.confidence)))
