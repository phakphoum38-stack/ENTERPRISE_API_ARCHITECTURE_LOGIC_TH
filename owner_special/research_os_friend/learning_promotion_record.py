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


class LearningPromotionRecordError(ValueError):
    pass


@dataclass(frozen=True)
class LearningPromotionRecordRequest:
    owner: str
    source_sha: str
    correlation_id: str
    skill_fingerprint: str
    result_fingerprint: str
    candidate_version: int
    binding_fingerprint: str
    eligibility_fingerprint: str
    record_id: str


class LearningPromotionRecordBoundary:
    """Create a deterministic, read-only record for H10 to evaluate later."""

    MAX_KEYS = 64
    MAX_DEPTH = 8

    def create(
        self,
        request: LearningPromotionRecordRequest,
        eligibility: dict[str, Any],
    ) -> dict[str, Any]:
        self._validate_request(request)
        self._validate_eligibility(eligibility)
        self._match(request, eligibility)
        candidate = eligibility["candidate"]
        self._scan(candidate, 0)

        payload = {
            "schema": "research-os-learning-promotion-record/v1",
            "record_id": request.record_id,
            "owner": request.owner,
            "source_sha": request.source_sha,
            "correlation_id": request.correlation_id,
            "skill_fingerprint": request.skill_fingerprint,
            "result_fingerprint": request.result_fingerprint,
            "candidate_version": request.candidate_version,
            "binding_fingerprint": request.binding_fingerprint,
            "eligibility_fingerprint": request.eligibility_fingerprint,
            "eligibility_decision": eligibility["promotion_eligibility"],
            "promotion_authority": "H10",
            "record_state": "READY_FOR_H10",
            "candidate": json.loads(json.dumps(candidate, sort_keys=True)),
            "read_only": True,
            "authority": "none",
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        payload["record_fingerprint"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return json.loads(json.dumps(payload, sort_keys=True))

    def _validate_request(self, request: LearningPromotionRecordRequest) -> None:
        if not request.owner or len(request.owner) > 128 or _BLOCKED.search(request.owner):
            raise LearningPromotionRecordError("invalid owner")
        if not _SHA_RE.fullmatch(request.source_sha):
            raise LearningPromotionRecordError("invalid source SHA")
        if not request.correlation_id or len(request.correlation_id) > 128 or _BLOCKED.search(request.correlation_id):
            raise LearningPromotionRecordError("invalid correlation id")
        if not _FP_RE.fullmatch(request.skill_fingerprint) or not _FP_RE.fullmatch(request.result_fingerprint):
            raise LearningPromotionRecordError("invalid fingerprint")
        if not isinstance(request.candidate_version, int) or isinstance(request.candidate_version, bool) or not 1 <= request.candidate_version <= 128:
            raise LearningPromotionRecordError("invalid candidate version")
        if not _FP_RE.fullmatch(request.binding_fingerprint) or not _FP_RE.fullmatch(request.eligibility_fingerprint):
            raise LearningPromotionRecordError("invalid contract fingerprint")
        if not request.record_id or len(request.record_id) > 128 or _BLOCKED.search(request.record_id):
            raise LearningPromotionRecordError("invalid record id")

    def _validate_eligibility(self, value: Any) -> None:
        if not isinstance(value, dict) or value.get("schema") != "research-os-learning-promotion-eligibility/v1":
            raise LearningPromotionRecordError("invalid eligibility envelope")
        if value.get("promotion_authority") != "H10":
            raise LearningPromotionRecordError("invalid promotion authority")
        if value.get("read_only") is not True or value.get("authority") != "none":
            raise LearningPromotionRecordError("eligibility authority contract violated")
        if value.get("promotion_eligibility") != "ELIGIBLE_FOR_H10":
            raise LearningPromotionRecordError("candidate is not eligible for H10")
        if not isinstance(value.get("candidate"), dict):
            raise LearningPromotionRecordError("missing candidate payload")

    def _match(self, request: LearningPromotionRecordRequest, eligibility: dict[str, Any]) -> None:
        for field in (
            "owner",
            "source_sha",
            "correlation_id",
            "skill_fingerprint",
            "result_fingerprint",
            "candidate_version",
            "binding_fingerprint",
        ):
            if getattr(request, field) != eligibility.get(field):
                raise LearningPromotionRecordError(f"eligibility {field} mismatch")
        if request.eligibility_fingerprint != eligibility.get("eligibility_fingerprint"):
            raise LearningPromotionRecordError("eligibility fingerprint mismatch")

    def _scan(self, value: Any, depth: int) -> None:
        if depth > self.MAX_DEPTH:
            raise LearningPromotionRecordError("candidate depth exceeds bounds")
        if isinstance(value, dict):
            if len(value) > self.MAX_KEYS:
                raise LearningPromotionRecordError("candidate object exceeds bounds")
            for key, item in value.items():
                if _BLOCKED.search(str(key)):
                    raise LearningPromotionRecordError("unsafe candidate key")
                self._scan(item, depth + 1)
        elif isinstance(value, list):
            if len(value) > self.MAX_KEYS:
                raise LearningPromotionRecordError("candidate list exceeds bounds")
            for item in value:
                self._scan(item, depth + 1)
        elif isinstance(value, str) and _BLOCKED.search(value):
            raise LearningPromotionRecordError("unsafe candidate value")
