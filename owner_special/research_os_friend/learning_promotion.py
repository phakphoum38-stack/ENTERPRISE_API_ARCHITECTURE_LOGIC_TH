"""Evidence-backed learning promotion policy for Research OS."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Mapping

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_BLOCKED = re.compile(r"(?:secret|token|password|private.?key|api.?key|credential|approval|authorize|release|merge|dispatch|shell|process|subprocess|mcp|computer.?use|exec|eval)", re.I)
_BLOCKED_VALUE = re.compile(r"(?:BEGIN [A-Z ]*PRIVATE KEY|gh[pousr]_|sk-proj-|javascript:|data:text/html|powershell|cmd(?:\.exe)?|bash -c|os\.system|subprocess)", re.I)


class LearningPromotionError(ValueError):
    """Raised when learned knowledge is unsafe or insufficiently evidenced."""


@dataclass(frozen=True)
class LearningCandidate:
    owner: str
    source_sha: str
    correlation_id: str
    name: str
    goal: str
    procedure: tuple[str, ...]
    evidence_fingerprint: str
    confidence: float
    core_skill: bool = False

    def __post_init__(self) -> None:
        if not self.owner or len(self.owner) > 256:
            raise LearningPromotionError("owner must be bounded")
        for value, label in ((self.source_sha, "source_sha"), (self.evidence_fingerprint, "evidence_fingerprint")):
            if label == "source_sha":
                if not isinstance(value, str) or not _SHA_RE.fullmatch(value):
                    raise LearningPromotionError("invalid source SHA")
            elif not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
                raise LearningPromotionError("invalid evidence fingerprint")
        for value, label in ((self.correlation_id, "correlation_id"), (self.name, "name"), (self.goal, "goal")):
            if not isinstance(value, str) or not value or len(value) > 2048 or _BLOCKED.search(value) or _BLOCKED_VALUE.search(value):
                raise LearningPromotionError(f"unsafe {label}")
        if not self.procedure or len(self.procedure) > 64:
            raise LearningPromotionError("procedure must be bounded and non-empty")
        if any(not isinstance(step, str) or not step or len(step) > 2048 or _BLOCKED.search(step) or _BLOCKED_VALUE.search(step) for step in self.procedure):
            raise LearningPromotionError("unsafe procedure")
        if not 0.0 <= self.confidence <= 1.0:
            raise LearningPromotionError("confidence must be between 0 and 1")
        if self.core_skill:
            raise LearningPromotionError("core skills cannot be promoted through learned-skill boundary")

    @property
    def fingerprint(self) -> str:
        material = {
            "owner": self.owner,
            "source_sha": self.source_sha,
            "correlation_id": self.correlation_id,
            "name": self.name,
            "goal": self.goal,
            "procedure": self.procedure,
            "evidence_fingerprint": self.evidence_fingerprint,
            "confidence": self.confidence,
        }
        return hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def evaluate_promotion(candidate: LearningCandidate, *, evidence_verified: bool, minimum_confidence: float = 0.8) -> bool:
    """Return true only when explicit verification evidence and confidence are present."""
    if not evidence_verified or candidate.confidence < minimum_confidence:
        return False
    if candidate.core_skill:
        return False
    return True


def snapshot_candidate(candidate: LearningCandidate) -> dict[str, Any]:
    """Return a detached, bounded projection of a learned candidate."""
    return {
        "schema": "research-os-learning-promotion/v1",
        "owner": candidate.owner,
        "source_sha": candidate.source_sha,
        "correlation_id": candidate.correlation_id,
        "name": candidate.name,
        "goal": candidate.goal,
        "procedure": list(candidate.procedure),
        "evidence_fingerprint": candidate.evidence_fingerprint,
        "confidence": candidate.confidence,
        "fingerprint": candidate.fingerprint,
        "read_only": True,
        "authority": "none",
    }
