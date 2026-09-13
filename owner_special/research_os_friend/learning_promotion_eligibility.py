from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_FP_RE = re.compile(r"^[0-9a-f]{64}$")
_BLOCKED = re.compile(
    r"(?:password|passwd|secret|token|api[_-]?key|credential|private[_-]?key|authorization|bearer|javascript:|data:text/html|powershell|cmd(?:\.exe)?|bash -c|os\.system|subprocess|shell|process|mcp|computer[_-]?use|release|merge|install|dispatch|bypass|approval|execute|executor)",
    re.I,
)


class LearningPromotionEligibilityError(ValueError):
    pass


@dataclass(frozen=True)
class LearningPromotionEligibilityRequest:
    owner: str
    source_sha: str
    correlation_id: str
    skill_fingerprint: str
    result_fingerprint: str
    candidate_version: int
    binding_fingerprint: str
    evidence_verified: bool
    quality_score: float


class LearningPromotionEligibilityBoundary:
    """Classify whether an integrity-verified candidate may enter H10 promotion evaluation."""

    MAX_KEYS = 64
    MAX_DEPTH = 8

    def evaluate(
        self,
        request: LearningPromotionEligibilityRequest,
        integrity: dict[str, Any],
    ) -> dict[str, Any]:
        self._validate_request(request)
        self._validate_integrity(integrity)
        self._match(request, integrity)
        candidate = integrity["candidate"]
        self._scan(candidate, 0)

        eligible = request.evidence_verified and request.quality_score >= 0.8
        decision = "ELIGIBLE_FOR_H10" if eligible else "NOT_ELIGIBLE"
        payload = {
            "schema": "research-os-learning-promotion-eligibility/v1",
            "owner": request.owner,
            "source_sha": request.source_sha,
            "correlation_id": request.correlation_id,
            "skill_fingerprint": request.skill_fingerprint,
            "result_fingerprint": request.result_fingerprint,
            "candidate_version": request.candidate_version,
            "binding_fingerprint": request.binding_fingerprint,
            "evidence_verified": request.evidence_verified,
            "quality_score": request.quality_score,
            "promotion_eligibility": decision,
            "promotion_authority": "H10",
            "candidate": json.loads(json.dumps(candidate, sort_keys=True)),
            "read_only": True,
            "authority": "none",
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        payload["eligibility_fingerprint"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return json.loads(json.dumps(payload, sort_keys=True))

    def _validate_request(self, request: LearningPromotionEligibilityRequest) -> None:
        if not request.owner or len(request.owner) > 128 or _BLOCKED.search(request.owner):
            raise LearningPromotionEligibilityError("invalid owner")
        if not _SHA_RE.fullmatch(request.source_sha):
            raise LearningPromotionEligibilityError("invalid source SHA")
        if not request.correlation_id or len(request.correlation_id) > 128 or _BLOCKED.search(request.correlation_id):
            raise LearningPromotionEligibilityError("invalid correlation id")
        if not _FP_RE.fullmatch(request.skill_fingerprint) or not _FP_RE.fullmatch(request.result_fingerprint):
            raise LearningPromotionEligibilityError("invalid fingerprint")
        if not isinstance(request.candidate_version, int) or isinstance(request.candidate_version, bool) or not 1 <= request.candidate_version <= 128:
            raise LearningPromotionEligibilityError("invalid candidate version")
        if not _FP_RE.fullmatch(request.binding_fingerprint):
            raise LearningPromotionEligibilityError("invalid binding fingerprint")
        if not isinstance(request.evidence_verified, bool):
            raise LearningPromotionEligibilityError("evidence verification must be boolean")
        if isinstance(request.quality_score, bool) or not isinstance(request.quality_score, (int, float)) or not 0.0 <= request.quality_score <= 1.0:
            raise LearningPromotionEligibilityError("quality score must be between 0 and 1")

    def _validate_integrity(self, value: Any) -> None:
        if not isinstance(value, dict) or value.get("schema") != "research-os-learning-candidate-integrity/v1":
            raise LearningPromotionEligibilityError("invalid integrity envelope")
        if value.get("integrity_verified") is not True:
            raise LearningPromotionEligibilityError("candidate integrity is not verified")
        if value.get("promotion_authority") != "H10":
            raise LearningPromotionEligibilityError("invalid promotion authority")
        if value.get("read_only") is not True or value.get("authority") != "none":
            raise LearningPromotionEligibilityError("integrity authority contract violated")
        if not isinstance(value.get("candidate"), dict):
            raise LearningPromotionEligibilityError("missing candidate payload")

    def _match(self, request: LearningPromotionEligibilityRequest, integrity: dict[str, Any]) -> None:
        for field in (
            "owner",
            "source_sha",
            "correlation_id",
            "skill_fingerprint",
            "result_fingerprint",
            "candidate_version",
            "binding_fingerprint",
        ):
            if getattr(request, field) != integrity.get(field):
                raise LearningPromotionEligibilityError(f"integrity {field} mismatch")

    def _scan(self, value: Any, depth: int) -> None:
        if depth > self.MAX_DEPTH:
            raise LearningPromotionEligibilityError("candidate depth exceeds bounds")
        if isinstance(value, dict):
            if len(value) > self.MAX_KEYS:
                raise LearningPromotionEligibilityError("candidate object exceeds bounds")
            for key, item in value.items():
                if _BLOCKED.search(str(key)):
                    raise LearningPromotionEligibilityError("unsafe candidate key")
                self._scan(item, depth + 1)
        elif isinstance(value, list):
            if len(value) > self.MAX_KEYS:
                raise LearningPromotionEligibilityError("candidate list exceeds bounds")
            for item in value:
                self._scan(item, depth + 1)
        elif isinstance(value, str) and _BLOCKED.search(value):
            raise LearningPromotionEligibilityError("unsafe candidate value")
