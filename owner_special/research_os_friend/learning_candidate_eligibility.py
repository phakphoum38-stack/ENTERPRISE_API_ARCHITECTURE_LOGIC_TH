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


class LearningCandidateEligibilityError(ValueError):
    pass


@dataclass(frozen=True)
class LearningCandidateEligibilityRequest:
    owner: str
    source_sha: str
    correlation_id: str
    skill_fingerprint: str
    result_fingerprint: str


class LearningCandidateEligibilityBoundary:
    MAX_KEYS = 64
    MAX_DEPTH = 8

    def evaluate(
        self,
        request: LearningCandidateEligibilityRequest,
        lifecycle: dict[str, Any],
    ) -> dict[str, Any]:
        self._validate_request(request)
        self._validate_lifecycle(lifecycle)
        self._match(request, lifecycle)

        result = lifecycle.get("result")
        self._scan(result, 0)
        candidate = {
            "schema": "research-os-learning-candidate-eligibility/v1",
            "owner": request.owner,
            "source_sha": request.source_sha,
            "correlation_id": request.correlation_id,
            "skill_fingerprint": request.skill_fingerprint,
            "result_fingerprint": request.result_fingerprint,
            "eligible": True,
            "learning_state": "LEARNED",
            "promotion_authority": "H10",
            "candidate": json.loads(json.dumps(result, sort_keys=True)),
            "read_only": True,
            "authority": "none",
        }
        canonical = json.dumps(candidate, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        candidate["eligibility_fingerprint"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return json.loads(json.dumps(candidate, sort_keys=True))

    def _validate_request(self, request: LearningCandidateEligibilityRequest) -> None:
        if not request.owner or len(request.owner) > 128 or _BLOCKED.search(request.owner):
            raise LearningCandidateEligibilityError("invalid owner")
        if not _SHA_RE.fullmatch(request.source_sha):
            raise LearningCandidateEligibilityError("invalid source SHA")
        if not request.correlation_id or len(request.correlation_id) > 128 or _BLOCKED.search(request.correlation_id):
            raise LearningCandidateEligibilityError("invalid correlation id")
        if not _FP_RE.fullmatch(request.skill_fingerprint) or not _FP_RE.fullmatch(request.result_fingerprint):
            raise LearningCandidateEligibilityError("invalid fingerprint")

    def _validate_lifecycle(self, value: Any) -> None:
        if not isinstance(value, dict) or value.get("schema") != "research-os-learning-lifecycle/v1":
            raise LearningCandidateEligibilityError("invalid lifecycle envelope")
        if value.get("read_only") is not True or value.get("authority") != "none":
            raise LearningCandidateEligibilityError("lifecycle authority contract violated")
        if value.get("result_status") != "SUCCEEDED" or value.get("learning_state") != "LEARNED":
            raise LearningCandidateEligibilityError("lifecycle result is not eligible")

    def _match(self, request: LearningCandidateEligibilityRequest, lifecycle: dict[str, Any]) -> None:
        for field in ("owner", "source_sha", "correlation_id", "skill_fingerprint", "result_fingerprint"):
            if getattr(request, field) != lifecycle.get(field):
                raise LearningCandidateEligibilityError(f"lifecycle {field} mismatch")

    def _scan(self, value: Any, depth: int) -> None:
        if depth > self.MAX_DEPTH:
            raise LearningCandidateEligibilityError("candidate depth exceeds bounds")
        if isinstance(value, dict):
            if len(value) > self.MAX_KEYS:
                raise LearningCandidateEligibilityError("candidate object exceeds bounds")
            for key, item in value.items():
                if _BLOCKED.search(str(key)):
                    raise LearningCandidateEligibilityError("unsafe candidate key")
                self._scan(item, depth + 1)
        elif isinstance(value, list):
            if len(value) > self.MAX_KEYS:
                raise LearningCandidateEligibilityError("candidate list exceeds bounds")
            for item in value:
                self._scan(item, depth + 1)
        elif isinstance(value, str) and _BLOCKED.search(value):
            raise LearningCandidateEligibilityError("unsafe candidate value")
