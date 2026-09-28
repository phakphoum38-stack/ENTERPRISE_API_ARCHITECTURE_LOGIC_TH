from __future__ import annotations

from dataclasses import dataclass
import copy
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


class LearningEvidenceProvenanceError(ValueError):
    pass


@dataclass(frozen=True)
class LearningEvidenceProvenanceRequest:
    owner: str
    source_sha: str
    skill_name: str
    skill_version: int
    correlation_id: str
    executor_result_fingerprint: str
    evidence_refs: tuple[str, ...]


class LearningEvidenceProvenanceBoundary:
    """Bind externally supplied evidence references to an executor result without fabricating evidence."""

    MAX_REFS = 64

    def bind(
        self,
        request: LearningEvidenceProvenanceRequest,
        executor_result: dict[str, Any],
    ) -> dict[str, Any]:
        self._validate_request(request)
        self._validate_result(executor_result)
        for field in ("owner", "source_sha", "skill_name", "skill_version", "correlation_id", "executor_result_fingerprint"):
            if getattr(request, field) != executor_result.get(field):
                raise LearningEvidenceProvenanceError(f"executor result {field} mismatch")
        if not request.evidence_refs:
            raise LearningEvidenceProvenanceError("at least one evidence reference is required")

        refs = tuple(request.evidence_refs)
        payload = {
            "schema": "research-os-learning-evidence-provenance/v1",
            "owner": request.owner,
            "source_sha": request.source_sha,
            "skill_name": request.skill_name,
            "skill_version": request.skill_version,
            "correlation_id": request.correlation_id,
            "executor_result_fingerprint": request.executor_result_fingerprint,
            "evidence_refs": refs,
            "evidence_state": "BOUND_EXTERNAL_REFERENCES",
            "provenance_authority": "none",
            "final_lifecycle_authority": "H27",
            "read_only": True,
            "authority": "none",
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        payload["provenance_fingerprint"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return copy.deepcopy(payload)

    def _validate_request(self, request: LearningEvidenceProvenanceRequest) -> None:
        if not request.owner or len(request.owner) > 128 or _BLOCKED.search(request.owner):
            raise LearningEvidenceProvenanceError("invalid owner")
        if not _SHA_RE.fullmatch(request.source_sha):
            raise LearningEvidenceProvenanceError("invalid source SHA")
        if not request.skill_name or len(request.skill_name) > 128 or _BLOCKED.search(request.skill_name):
            raise LearningEvidenceProvenanceError("invalid skill name")
        if not isinstance(request.skill_version, int) or isinstance(request.skill_version, bool) or not 1 <= request.skill_version <= 128:
            raise LearningEvidenceProvenanceError("invalid skill version")
        if not request.correlation_id or len(request.correlation_id) > 128 or _BLOCKED.search(request.correlation_id):
            raise LearningEvidenceProvenanceError("invalid correlation id")
        if not _FP_RE.fullmatch(request.executor_result_fingerprint):
            raise LearningEvidenceProvenanceError("invalid executor result fingerprint")
        if len(request.evidence_refs) > self.MAX_REFS:
            raise LearningEvidenceProvenanceError("too many evidence references")
        for ref in request.evidence_refs:
            if not isinstance(ref, str) or not ref or len(ref) > 512 or _BLOCKED.search(ref):
                raise LearningEvidenceProvenanceError("invalid evidence reference")

    def _validate_result(self, value: Any) -> None:
        if not isinstance(value, dict) or value.get("schema") != "research-os-learning-executor-result/v1":
            raise LearningEvidenceProvenanceError("invalid executor result envelope")
        if value.get("read_only") is not True or value.get("authority") != "none":
            raise LearningEvidenceProvenanceError("executor result authority contract violated")
        if not _FP_RE.fullmatch(str(value.get("executor_result_fingerprint", ""))):
            raise LearningEvidenceProvenanceError("invalid executor result fingerprint")
