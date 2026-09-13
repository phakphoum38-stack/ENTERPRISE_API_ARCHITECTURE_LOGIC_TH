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


class LearningCandidateVersionBindingError(ValueError):
    pass


@dataclass(frozen=True)
class LearningCandidateVersionBindingRequest:
    owner: str
    source_sha: str
    correlation_id: str
    skill_fingerprint: str
    result_fingerprint: str
    candidate_version: int


class LearningCandidateVersionBindingBoundary:
    MAX_KEYS = 64
    MAX_DEPTH = 8

    def bind(
        self,
        request: LearningCandidateVersionBindingRequest,
        candidate: dict[str, Any],
    ) -> dict[str, Any]:
        self._validate_request(request)
        self._validate_candidate(candidate)
        self._match(request, candidate)
        payload = {
            "schema": "research-os-learning-candidate-version-binding/v1",
            "owner": request.owner,
            "source_sha": request.source_sha,
            "correlation_id": request.correlation_id,
            "skill_fingerprint": request.skill_fingerprint,
            "result_fingerprint": request.result_fingerprint,
            "candidate_version": request.candidate_version,
            "eligible": True,
            "promotion_authority": "H10",
            "candidate": json.loads(json.dumps(candidate.get("candidate"), sort_keys=True)),
            "read_only": True,
            "authority": "none",
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        payload["binding_fingerprint"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return json.loads(json.dumps(payload, sort_keys=True))

    def _validate_request(self, request: LearningCandidateVersionBindingRequest) -> None:
        if not request.owner or len(request.owner) > 128 or _BLOCKED.search(request.owner):
            raise LearningCandidateVersionBindingError("invalid owner")
        if not _SHA_RE.fullmatch(request.source_sha):
            raise LearningCandidateVersionBindingError("invalid source SHA")
        if not request.correlation_id or len(request.correlation_id) > 128 or _BLOCKED.search(request.correlation_id):
            raise LearningCandidateVersionBindingError("invalid correlation id")
        if not _FP_RE.fullmatch(request.skill_fingerprint) or not _FP_RE.fullmatch(request.result_fingerprint):
            raise LearningCandidateVersionBindingError("invalid fingerprint")
        if not isinstance(request.candidate_version, int) or isinstance(request.candidate_version, bool) or request.candidate_version < 1 or request.candidate_version > 128:
            raise LearningCandidateVersionBindingError("invalid candidate version")

    def _validate_candidate(self, value: Any) -> None:
        if not isinstance(value, dict) or value.get("schema") != "research-os-learning-candidate-eligibility/v1":
            raise LearningCandidateVersionBindingError("invalid eligibility envelope")
        if value.get("eligible") is not True or value.get("learning_state") != "LEARNED":
            raise LearningCandidateVersionBindingError("candidate is not eligible")
        if value.get("promotion_authority") != "H10":
            raise LearningCandidateVersionBindingError("invalid promotion authority")
        if value.get("read_only") is not True or value.get("authority") != "none":
            raise LearningCandidateVersionBindingError("eligibility authority contract violated")
        if "candidate" not in value or not isinstance(value["candidate"], dict):
            raise LearningCandidateVersionBindingError("missing candidate payload")
        self._scan(value["candidate"], 0)

    def _match(self, request: LearningCandidateVersionBindingRequest, candidate: dict[str, Any]) -> None:
        for field in ("owner", "source_sha", "correlation_id", "skill_fingerprint", "result_fingerprint"):
            if getattr(request, field) != candidate.get(field):
                raise LearningCandidateVersionBindingError(f"candidate {field} mismatch")
        if candidate.get("candidate_version") != request.candidate_version:
            raise LearningCandidateVersionBindingError("candidate version mismatch")

    def _scan(self, value: Any, depth: int) -> None:
        if depth > self.MAX_DEPTH:
            raise LearningCandidateVersionBindingError("candidate depth exceeds bounds")
        if isinstance(value, dict):
            if len(value) > self.MAX_KEYS:
                raise LearningCandidateVersionBindingError("candidate object exceeds bounds")
            for key, item in value.items():
                if _BLOCKED.search(str(key)):
                    raise LearningCandidateVersionBindingError("unsafe candidate key")
                self._scan(item, depth + 1)
        elif isinstance(value, list):
            if len(value) > self.MAX_KEYS:
                raise LearningCandidateVersionBindingError("candidate list exceeds bounds")
            for item in value:
                self._scan(item, depth + 1)
        elif isinstance(value, str) and _BLOCKED.search(value):
            raise LearningCandidateVersionBindingError("unsafe candidate value")
