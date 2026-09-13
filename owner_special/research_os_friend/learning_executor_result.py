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
_ALLOWED = {"SUCCEEDED", "FAILED", "BLOCKED"}


class LearningExecutorResultError(ValueError):
    pass


@dataclass(frozen=True)
class LearningExecutorResultRequest:
    owner: str
    source_sha: str
    skill_name: str
    skill_version: int
    activation_fingerprint: str
    correlation_id: str
    status: str


class LearningExecutorResultBoundary:
    """Classify a runtime result produced after H24 activation without executing anything."""

    MAX_KEYS = 64
    MAX_DEPTH = 8

    def classify(
        self,
        request: LearningExecutorResultRequest,
        activation: dict[str, Any],
        result: dict[str, Any],
    ) -> dict[str, Any]:
        self._validate_request(request)
        self._validate_activation(activation)
        if not isinstance(result, dict):
            raise LearningExecutorResultError("runtime result must be an object")
        for field in ("owner", "skill_name", "skill_version", "activation_fingerprint", "correlation_id"):
            if getattr(request, field) != activation.get(field):
                raise LearningExecutorResultError(f"activation {field} mismatch")
        if request.status not in _ALLOWED:
            raise LearningExecutorResultError("invalid runtime status")
        if result.get("status") not in _ALLOWED:
            raise LearningExecutorResultError("invalid result status")
        if result.get("status") != request.status:
            raise LearningExecutorResultError("runtime result status mismatch")

        self._scan(result, 0)
        result_copy = json.loads(json.dumps(result, sort_keys=True))
        canonical = json.dumps(result_copy, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        result_fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        payload = {
            "schema": "research-os-learning-executor-result/v1",
            "owner": request.owner,
            "source_sha": request.source_sha,
            "skill_name": request.skill_name,
            "skill_version": request.skill_version,
            "activation_fingerprint": request.activation_fingerprint,
            "correlation_id": request.correlation_id,
            "status": request.status,
            "result": result_copy,
            "result_fingerprint": result_fingerprint,
            "evidence_authority": "H26",
            "read_only": True,
            "authority": "none",
        }
        envelope = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        payload["executor_result_fingerprint"] = hashlib.sha256(envelope.encode("utf-8")).hexdigest()
        return json.loads(json.dumps(payload, sort_keys=True))

    def _validate_request(self, request: LearningExecutorResultRequest) -> None:
        if not request.owner or len(request.owner) > 128 or _BLOCKED.search(request.owner):
            raise LearningExecutorResultError("invalid owner")
        if not _SHA_RE.fullmatch(request.source_sha):
            raise LearningExecutorResultError("invalid source SHA")
        if not request.skill_name or len(request.skill_name) > 128 or _BLOCKED.search(request.skill_name):
            raise LearningExecutorResultError("invalid skill name")
        if not isinstance(request.skill_version, int) or isinstance(request.skill_version, bool) or not 1 <= request.skill_version <= 128:
            raise LearningExecutorResultError("invalid skill version")
        if not _FP_RE.fullmatch(request.activation_fingerprint):
            raise LearningExecutorResultError("invalid activation fingerprint")
        if not request.correlation_id or len(request.correlation_id) > 128 or _BLOCKED.search(request.correlation_id):
            raise LearningExecutorResultError("invalid correlation id")

    def _validate_activation(self, value: Any) -> None:
        if not isinstance(value, dict) or value.get("schema") != "research-os-learning-skill-activation/v1":
            raise LearningExecutorResultError("invalid activation envelope")
        if value.get("activation_state") != "READY_FOR_H25":
            raise LearningExecutorResultError("activation is not ready")
        if value.get("execution_authority") != "H25":
            raise LearningExecutorResultError("invalid execution authority")
        if value.get("read_only") is not True or value.get("authority") != "none":
            raise LearningExecutorResultError("activation authority contract violated")

    def _scan(self, value: Any, depth: int) -> None:
        if depth > self.MAX_DEPTH:
            raise LearningExecutorResultError("result depth exceeds bounds")
        if isinstance(value, dict):
            if len(value) > self.MAX_KEYS:
                raise LearningExecutorResultError("result object exceeds bounds")
            for key, item in value.items():
                if _BLOCKED.search(str(key)):
                    raise LearningExecutorResultError("unsafe result key")
                self._scan(item, depth + 1)
        elif isinstance(value, list):
            if len(value) > self.MAX_KEYS:
                raise LearningExecutorResultError("result list exceeds bounds")
            for item in value:
                self._scan(item, depth + 1)
        elif isinstance(value, str) and _BLOCKED.search(value):
            raise LearningExecutorResultError("unsafe result value")
