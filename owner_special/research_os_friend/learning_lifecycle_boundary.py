from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_FP_RE = re.compile(r"^[0-9a-f]{64}$")
_BLOCKED = re.compile(r"(?:password|passwd|secret|token|api[_-]?key|credential|private[_-]?key|authorization|bearer|javascript:|data:text/html|powershell|cmd(?:\.exe)?|bash -c|os\.system|subprocess|shell|process|mcp|computer[_-]?use|release|merge|install|dispatch|bypass|approval)", re.I)


class LearningLifecycleError(ValueError):
    pass


@dataclass(frozen=True)
class LearningLifecycleRequest:
    owner: str
    source_sha: str
    correlation_id: str
    skill_fingerprint: str
    result_fingerprint: str
    result_status: str
    result: dict[str, Any]


class LearningLifecycleBoundary:
    MAX_KEYS = 64
    MAX_DEPTH = 8
    ALLOWED_RESULTS = frozenset({"SUCCEEDED", "FAILED", "BLOCKED"})

    def classify(self, request: LearningLifecycleRequest, expected_result: dict[str, Any]) -> dict[str, Any]:
        self._validate_request(request)
        self._validate_expected(expected_result)
        self._match(request, expected_result)
        self._scan(request.result, 0)
        state = {
            "SUCCEEDED": "LEARNED",
            "FAILED": "FAILED",
            "BLOCKED": "BLOCKED",
        }[request.result_status]
        payload = {
            "schema": "research-os-learning-lifecycle/v1",
            "owner": request.owner,
            "source_sha": request.source_sha,
            "correlation_id": request.correlation_id,
            "skill_fingerprint": request.skill_fingerprint,
            "result_fingerprint": request.result_fingerprint,
            "result_status": request.result_status,
            "learning_state": state,
            "result": json.loads(json.dumps(request.result, sort_keys=True)),
            "read_only": True,
            "authority": "none",
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        payload["lifecycle_fingerprint"] = hashlib.sha256(canonical.encode()).hexdigest()
        return json.loads(json.dumps(payload, sort_keys=True))

    def _validate_request(self, request: LearningLifecycleRequest) -> None:
        if not request.owner or len(request.owner) > 128 or _BLOCKED.search(request.owner):
            raise LearningLifecycleError("invalid owner")
        if not _SHA_RE.fullmatch(request.source_sha):
            raise LearningLifecycleError("invalid source SHA")
        if not request.correlation_id or len(request.correlation_id) > 128 or _BLOCKED.search(request.correlation_id):
            raise LearningLifecycleError("invalid correlation id")
        if not _FP_RE.fullmatch(request.skill_fingerprint) or not _FP_RE.fullmatch(request.result_fingerprint):
            raise LearningLifecycleError("invalid fingerprint")
        if request.result_status not in self.ALLOWED_RESULTS:
            raise LearningLifecycleError("invalid result status")

    def _validate_expected(self, value: Any) -> None:
        if not isinstance(value, dict) or value.get("schema") != "research-os-executor-result/v1":
            raise LearningLifecycleError("invalid executor result envelope")
        if value.get("read_only") is not True or value.get("authority") != "none":
            raise LearningLifecycleError("executor result authority contract violated")

    def _match(self, request: LearningLifecycleRequest, expected: dict[str, Any]) -> None:
        for field in ("owner", "source_sha", "correlation_id", "skill_fingerprint", "result_fingerprint"):
            if getattr(request, field) != expected.get(field):
                raise LearningLifecycleError(f"result {field} mismatch")
        if request.result_status != expected.get("status"):
            raise LearningLifecycleError("result result_status mismatch")

    def _scan(self, value: Any, depth: int) -> None:
        if depth > self.MAX_DEPTH:
            raise LearningLifecycleError("result depth exceeds bounds")
        if isinstance(value, dict):
            if len(value) > self.MAX_KEYS:
                raise LearningLifecycleError("result object exceeds bounds")
            for key, item in value.items():
                if _BLOCKED.search(str(key)):
                    raise LearningLifecycleError("unsafe result key")
                self._scan(item, depth + 1)
        elif isinstance(value, list):
            if len(value) > self.MAX_KEYS:
                raise LearningLifecycleError("result list exceeds bounds")
            for item in value:
                self._scan(item, depth + 1)
        elif isinstance(value, str) and _BLOCKED.search(value):
            raise LearningLifecycleError("unsafe result value")
