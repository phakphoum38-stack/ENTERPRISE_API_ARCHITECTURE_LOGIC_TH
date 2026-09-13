from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_FP_RE = re.compile(r"^[0-9a-f]{64}$")
_BLOCKED = re.compile(r"(?:password|passwd|secret|token|api[_-]?key|credential|private[_-]?key|authorization|bearer|javascript:|data:text/html|powershell|cmd(?:\.exe)?|bash -c|os\.system|subprocess|shell|process|mcp|computer[_-]?use|release|merge|install|dispatch|bypass|approval)", re.I)


class ExecutorResultError(ValueError):
    pass


@dataclass(frozen=True)
class ExecutorResultRequest:
    owner: str
    source_sha: str
    correlation_id: str
    skill_fingerprint: str
    handoff_fingerprint: str
    status: str
    result: dict[str, Any]


class ExecutorResultBoundary:
    MAX_CORRELATION = 128
    MAX_KEYS = 64
    ALLOWED_STATUS = frozenset({"SUCCEEDED", "FAILED", "BLOCKED"})

    def accept(self, request: ExecutorResultRequest, expected_handoff: dict[str, Any]) -> dict[str, Any]:
        self._validate_request(request)
        self._validate_handoff(expected_handoff)
        self._validate_result(request.result)
        self._match_identity(request, expected_handoff)
        payload = {
            "schema": "research-os-executor-result/v1",
            "owner": request.owner,
            "source_sha": request.source_sha,
            "correlation_id": request.correlation_id,
            "skill_fingerprint": request.skill_fingerprint,
            "handoff_fingerprint": request.handoff_fingerprint,
            "status": request.status,
            "result": json.loads(json.dumps(request.result, sort_keys=True)),
            "read_only": True,
            "authority": "none",
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        payload["result_fingerprint"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return json.loads(json.dumps(payload, sort_keys=True))

    def _validate_request(self, request: ExecutorResultRequest) -> None:
        if not request.owner or len(request.owner) > 128 or _BLOCKED.search(request.owner):
            raise ExecutorResultError("invalid owner")
        if not _SHA_RE.fullmatch(request.source_sha):
            raise ExecutorResultError("invalid source SHA")
        if not request.correlation_id or len(request.correlation_id) > self.MAX_CORRELATION or _BLOCKED.search(request.correlation_id):
            raise ExecutorResultError("invalid correlation id")
        for value, label in ((request.skill_fingerprint, "skill fingerprint"), (request.handoff_fingerprint, "handoff fingerprint")):
            if not _FP_RE.fullmatch(value):
                raise ExecutorResultError(f"invalid {label}")
        if request.status not in self.ALLOWED_STATUS:
            raise ExecutorResultError("invalid result status")

    def _validate_handoff(self, handoff: Any) -> None:
        if not isinstance(handoff, dict) or handoff.get("schema") != "research-os-executor-handoff/v1":
            raise ExecutorResultError("invalid handoff")
        if handoff.get("handoff") != "HANDOFF_READY":
            raise ExecutorResultError("handoff is not ready")
        if handoff.get("read_only") is not True or handoff.get("authority") != "none":
            raise ExecutorResultError("handoff authority contract violated")

    def _match_identity(self, request: ExecutorResultRequest, handoff: dict[str, Any]) -> None:
        fields = ("owner", "source_sha", "correlation_id", "skill_fingerprint")
        for field in fields:
            if request.__dict__[field] != handoff.get(field):
                raise ExecutorResultError(f"handoff {field} mismatch")
        if request.handoff_fingerprint != handoff.get("handoff_fingerprint"):
            raise ExecutorResultError("handoff fingerprint mismatch")

    def _validate_result(self, value: Any) -> None:
        if not isinstance(value, dict) or len(value) > self.MAX_KEYS:
            raise ExecutorResultError("invalid or oversized result")
        self._scan(value, depth=0)

    def _scan(self, value: Any, depth: int) -> None:
        if depth > 8:
            raise ExecutorResultError("result depth exceeds bounds")
        if isinstance(value, dict):
            if len(value) > self.MAX_KEYS:
                raise ExecutorResultError("result object exceeds bounds")
            for key, item in value.items():
                if _BLOCKED.search(str(key)):
                    raise ExecutorResultError("unsafe result key")
                self._scan(item, depth + 1)
        elif isinstance(value, list):
            if len(value) > self.MAX_KEYS:
                raise ExecutorResultError("result list exceeds bounds")
            for item in value:
                self._scan(item, depth + 1)
        elif isinstance(value, str) and _BLOCKED.search(value):
            raise ExecutorResultError("unsafe result value")
