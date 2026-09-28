from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re

from .models import LearnedSkillCandidate


@dataclass(frozen=True)
class LearningObservation:
    owner_id: str
    trigger: str
    outcome: str
    evidence_refs: tuple[str, ...] = ()
    context: tuple[tuple[str, str], ...] = ()

    def fingerprint(self) -> str:
        payload = {
            "owner_id": self.owner_id.strip(),
            "trigger": self.trigger.strip(),
            "outcome": self.outcome.strip(),
            "evidence_refs": self.evidence_refs,
            "context": self.context,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class LearningPattern:
    observation_fingerprint: str
    trigger: str
    outcome: str


@dataclass(frozen=True)
class LearningSandbox:
    candidate: LearnedSkillCandidate
    sandbox_id: str
    isolated: bool = True


class LearningObservationPipeline:
    """Deterministic data-only observation-to-sandbox boundary."""

    def observe(self, observation: LearningObservation) -> LearningPattern:
        if not observation.owner_id.strip() or not observation.trigger.strip():
            raise ValueError("owner and trigger are required")
        if len(observation.evidence_refs) > 16:
            raise ValueError("too many evidence references")
        return LearningPattern(
            observation_fingerprint=observation.fingerprint(),
            trigger=observation.trigger.strip(),
            outcome=observation.outcome.strip(),
        )

    def candidate(
        self,
        pattern: LearningPattern,
        *,
        name: str,
        goal: str,
        procedure: tuple[str, ...],
        evidence: tuple[str, ...],
        confidence: float,
    ) -> LearnedSkillCandidate:
        if not re.fullmatch(r"[0-9a-f]{64}", pattern.observation_fingerprint):
            raise ValueError("invalid observation fingerprint")
        return LearnedSkillCandidate(
            name=name.strip(),
            goal=goal.strip(),
            procedure=procedure,
            evidence=evidence,
            confidence=confidence,
            metadata={"observation_fingerprint": pattern.observation_fingerprint},
        )

    def sandbox(self, candidate: LearnedSkillCandidate) -> LearningSandbox:
        payload = json.dumps(
            {
                "name": candidate.name,
                "version": candidate.version,
                "procedure": candidate.procedure,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        sandbox_id = hashlib.sha256(payload).hexdigest()
        return LearningSandbox(candidate=candidate, sandbox_id=sandbox_id)
