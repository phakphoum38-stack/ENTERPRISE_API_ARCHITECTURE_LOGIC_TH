from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_FP_RE = re.compile(r"^[0-9a-f]{64}$")
_BLOCKED = re.compile(
    r"(?:password|passwd|secret|token|api[_-]?key|credential|private[_-]?key|authorization|bearer|release|merge|install|dispatch|bypass|shell|process|subprocess|mcp|computer[_-]?use|exec|eval)",
    re.I,
)
_BLOCKED_VALUE = re.compile(
    r"(?:sk-[A-Za-z0-9_-]{8,}|-----BEGIN [A-Z ]+ PRIVATE KEY-----|javascript:|data:text/html|powershell|cmd(?:\.exe)?|bash -c|os\.system|subprocess)",
    re.I,
)


class ExecutorHandoffError(ValueError):
    pass


@dataclass(frozen=True)
class ExecutorHandoffRequest:
    owner: str
    source_sha: str
    correlation_id: str
    skill_fingerprint: str
    activation_decision: str
    capability: str


class ExecutorHandoffBoundary:
    """Build a bounded handoff envelope without invoking an executor."""

    ALLOWED_CAPABILITIES = frozenset({"LEARNED_SKILL_EXECUTOR", "LEARNED_SKILL_INSPECTOR"})
    MAX_CORRELATION = 128

    def handoff(self, request: ExecutorHandoffRequest, skill: dict[str, Any]) -> dict[str, Any]:
        self._validate_request(request)
        self._validate_skill(skill)
        if request.activation_decision != "ALLOW_ACTIVATION":
            raise ExecutorHandoffError("activation decision does not permit executor handoff")
        if request.capability != "LEARNED_SKILL_EXECUTOR":
            raise ExecutorHandoffError("executor capability is not allowlisted")

        payload = {
            "schema": "research-os-executor-handoff/v1",
            "owner": request.owner,
            "source_sha": request.source_sha,
            "correlation_id": request.correlation_id,
            "skill_fingerprint": request.skill_fingerprint,
            "activation_decision": request.activation_decision,
            "capability": request.capability,
            "skill": json.loads(json.dumps(skill, sort_keys=True)),
            "handoff": "HANDOFF_READY",
            "read_only": True,
            "authority": "none",
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        payload["handoff_fingerprint"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return json.loads(json.dumps(payload, sort_keys=True))

    def _validate_request(self, request: ExecutorHandoffRequest) -> None:
        if not request.owner or len(request.owner) > 128 or _BLOCKED.search(request.owner):
            raise ExecutorHandoffError("invalid owner")
        if not _SHA_RE.fullmatch(request.source_sha):
            raise ExecutorHandoffError("invalid source SHA")
        if not request.correlation_id or len(request.correlation_id) > self.MAX_CORRELATION:
            raise ExecutorHandoffError("invalid correlation id")
        if _BLOCKED.search(request.correlation_id) or _BLOCKED_VALUE.search(request.correlation_id):
            raise ExecutorHandoffError("unsafe correlation id")
        if not _FP_RE.fullmatch(request.skill_fingerprint):
            raise ExecutorHandoffError("invalid skill fingerprint")
        if request.activation_decision not in {"ALLOW_ACTIVATION", "ALLOW_INSPECTION", "REQUIRE_APPROVAL", "DENY"}:
            raise ExecutorHandoffError("invalid activation decision")
        if request.capability not in self.ALLOWED_CAPABILITIES:
            raise ExecutorHandoffError("unsupported executor capability")

    def _validate_skill(self, skill: Any) -> None:
        if not isinstance(skill, dict) or len(skill) > 64:
            raise ExecutorHandoffError("invalid or oversized skill")
        self._scan(skill)

    def _scan(self, value: Any) -> None:
        if isinstance(value, dict):
            if len(value) > 64:
                raise ExecutorHandoffError("skill object exceeds bounds")
            for key, item in value.items():
                if _BLOCKED.search(str(key)):
                    raise ExecutorHandoffError("unsafe skill key")
                self._scan(item)
        elif isinstance(value, list):
            if len(value) > 64:
                raise ExecutorHandoffError("skill list exceeds bounds")
            for item in value:
                self._scan(item)
        elif isinstance(value, str) and (_BLOCKED.search(value) or _BLOCKED_VALUE.search(value)):
            raise ExecutorHandoffError("unsafe skill value")
