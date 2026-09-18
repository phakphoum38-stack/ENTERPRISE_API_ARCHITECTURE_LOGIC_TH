from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re

from .test_evidence import LearningEvidence


_SHA256 = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class LearningConfidence:
    """Deterministic confidence projection from validated learning evidence."""

    confidence_id: str
    evidence_ids: tuple[str, ...]
    passed_count: int
    evidence_count: int
    score: float
    status: str
    evidence_fingerprint: str
    mathematical_root: str
    coverage_model: str


class EvidenceConfidenceBoundary:
    """Data-only Evidence -> Confidence projection.

    The confidence score is a finite projection of evidence within the shared
    10^1000 logical coverage model. The root is mathematical; evidence remains
    finite and deterministic.

    This boundary never executes candidates, promotes skills, mutates Core
    Skills, schedules work, or changes execution/worker/queue behavior.
    """

    MATHEMATICAL_ROOT = "10^1000"
    COVERAGE_MODEL = "logical_cartesian_product"

    def derive(self, evidence: LearningEvidence) -> LearningConfidence:
        return self.aggregate((evidence,))

    def aggregate(self, evidence: tuple[LearningEvidence, ...]) -> LearningConfidence:
        if not evidence:
            raise ValueError("evidence is required")

        ordered = tuple(sorted(
            evidence,
            key=lambda item: (item.evidence_id, item.test_id, item.sandbox_id),
        ))
        self._validate(ordered)

        passed_count = sum(1 for item in ordered if item.passed)
        evidence_count = len(ordered)
        score = passed_count / evidence_count
        status = "CONFIDENT" if score > 0.0 else "HOLD"

        payload = [{
            "evidence_id": item.evidence_id,
            "test_id": item.test_id,
            "sandbox_id": item.sandbox_id,
            "result_hash": item.result_hash,
            "passed": item.passed,
        } for item in ordered]
        evidence_fingerprint = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

        identity = {
            "type": "learning_confidence",
            "mathematical_root": self.MATHEMATICAL_ROOT,
            "coverage_model": self.COVERAGE_MODEL,
            "evidence_fingerprint": evidence_fingerprint,
            "evidence_ids": [item.evidence_id for item in ordered],
            "passed_count": passed_count,
            "evidence_count": evidence_count,
            "score": score,
            "status": status,
        }
        confidence_id = hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

        return LearningConfidence(
            confidence_id=confidence_id,
            evidence_ids=tuple(item.evidence_id for item in ordered),
            passed_count=passed_count,
            evidence_count=evidence_count,
            score=score,
            status=status,
            evidence_fingerprint=evidence_fingerprint,
            mathematical_root=self.MATHEMATICAL_ROOT,
            coverage_model=self.COVERAGE_MODEL,
        )

    @staticmethod
    def _validate(evidence: tuple[LearningEvidence, ...]) -> None:
        for item in evidence:
            if not _SHA256.fullmatch(item.evidence_id):
                raise ValueError("invalid evidence_id")
            if not _SHA256.fullmatch(item.test_id):
                raise ValueError("invalid test_id")
            if not item.sandbox_id.strip():
                raise ValueError("sandbox_id is required")
            if not _SHA256.fullmatch(item.result_hash):
                raise ValueError("invalid result_hash")
            if not isinstance(item.passed, bool):
                raise ValueError("evidence passed state must be boolean")
