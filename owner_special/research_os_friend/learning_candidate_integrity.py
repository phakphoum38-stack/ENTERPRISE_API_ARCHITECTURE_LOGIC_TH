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


class LearningCandidateIntegrityError(ValueError):
    pass


@dataclass(frozen=True)
class LearningCandidateIntegrityRequest:
    owner: str
    source_sha: str
    correlation_id: str
    skill_fingerprint: str
    result_fingerprint: str
    candidate_version: int
    binding_fingerprint: str


class LearningCandidateIntegrityBoundary:
    MAX_KEYS = 64
    MAX_DEPTH = 8

    def verify(
        self,
        request: LearningCandidateIntegrityRequest,
        binding: dict[str, Any],
    ) -> dict[str, Any]:
        self._validate_request(request)
        self._validate_binding(binding)
        self._match(request, binding)

        unsigned = dict(binding)
        unsigned.pop("binding_fingerprint", None)
        canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        if expected != request.binding_fingerprint:
            raise LearningCandidateIntegrityError("binding fingerprint mismatch")

        payload = {
            "schema": "research-os-learning-candidate-integrity/v1",
            "owner": request.owner,
            "source_sha": request.source_sha,
            "correlation_id": request.correlation_id,
            "skill_fingerprint": request.skill_fingerprint,
            "result_fingerprint": request.result_fingerprint,
            "candidate_version": request.candidate_version,
            "binding_fingerprint": request.binding_fingerprint,
            "integrity_verified": True,
            "promotion_authority": "H10",
            "read_only": True,
            "authority": "none",
        }
        payload["integrity_fingerprint"] = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        ).hexdigest()
        return json.loads(json.dumps(payload, sort_keys=True))

    def _validate_request(self, request: LearningCandidateIntegrityRequest) -> None:
        if not request.owner or len(request.owner) > 128 or _BLOCKED.search(request.owner):
            raise LearningCandidateIntegrityError("invalid owner")
        if not _SHA_RE.fullmatch(request.source_sha):
            raise LearningCandidateIntegrityError("invalid source SHA")
        if not request.correlation_id or len(request.correlation_id) > 128 or _BLOCKED.search(request.correlation_id):
            raise LearningCandidateIntegrityError("invalid correlation id")
        if not _FP_RE.fullmatch(request.skill_fingerprint) or not _FP_RE.fullmatch(request.result_fingerprint):
            raise LearningCandidateIntegrityError("invalid fingerprint")
        if not isinstance(request.candidate_version, int) or isinstance(request.candidate_version, bool) or not 1 <= request.candidate_version <= 128:
            raise LearningCandidateIntegrityError("invalid candidate version")
        if not _FP_RE.fullmatch(request.binding_fingerprint):
            raise LearningCandidateIntegrityError("invalid binding fingerprint")

    def _validate_binding(self, value: Any) -> None:
        if not isinstance(value, dict) or value.get("schema") != "research-os-learning-candidate-version-binding/v1":
            raise LearningCandidateIntegrityError("invalid version binding envelope")
        if value.get("eligible") is not True or value.get("promotion_authority") != "H10":
            raise LearningCandidateIntegrityError("invalid bound candidate")
        if value.get("read_only") is not True or value.get("authority") != "none":
            raise LearningCandidateIntegrityError("binding authority contract violated")
        if "candidate" not in value or not isinstance(value["candidate"], dict):
            raise LearningCandidateIntegrityError("missing candidate payload")
        self._scan(value["candidate"], 0)

    def _match(self, request: LearningCandidateIntegrityRequest, binding: dict[str, Any]) -> None:
        for field in ("owner", "source_sha", "correlation_id", "skill_fingerprint", "result_fingerprint", "candidate_version"):
            if getattr(request, field) != binding.get(field):
                raise LearningCandidateIntegrityError(f"binding {field} mismatch")

    def _scan(self, value: Any, depth: int) -> None:
        if depth > self.MAX_DEPTH:
            raise LearningCandidateIntegrityError("candidate depth exceeds bounds")
        if isinstance(value, dict):
            if len(value) > self.MAX_KEYS:
                raise LearningCandidateIntegrityError("candidate object exceeds bounds")
            for key, item in value.items():
                if _BLOCKED.search(str(key)):
                    raise LearningCandidateIntegrityError("unsafe candidate key")
                self._scan(item, depth + 1)
        elif isinstance(value, list):
            if len(value) > self.MAX_KEYS:
                raise LearningCandidateIntegrityError("candidate list exceeds bounds")
            for item in value:
                self._scan(item, depth + 1)
        elif isinstance(value, str) and _BLOCKED.search(value):
            raise LearningCandidateIntegrityError("unsafe candidate value")
