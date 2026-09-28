from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re
from typing import Any


_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_FP_RE = re.compile(r"^[0-9a-f]{64}$")
_BLOCKED = re.compile(
    r"(?:password|passwd|secret|token|api[_-]?key|credential|private[_-]?key|access[_-]?token|authorization|bearer|approval|release|merge|install|dispatch|bypass|execute|shell|process|mcp|computer[_-]?use)",
    re.IGNORECASE,
)
_BLOCKED_VALUE = re.compile(r"(?:sk-[A-Za-z0-9_-]{8,}|-----BEGIN [A-Z ]+ PRIVATE KEY-----|api[_-]?key\s*=)", re.IGNORECASE)


class LearningActivationError(ValueError):
    pass


@dataclass(frozen=True)
class LearningActivationRequest:
    owner: str
    source_sha: str
    correlation_id: str
    skill_fingerprint: str
    intent: str = "inspect"
    h12_decision: str = "ALLOW_INSPECTION"
    approval_state: str = "NOT_REQUIRED"


class LearningSkillActivator:
    """Authorize a learned-skill activation intent without executing it."""

    MAX_CORRELATION = 128
    MAX_SKILL_KEYS = 64

    def __init__(self, registry: Any, consumption: Any) -> None:
        self._registry = registry
        self._consumption = consumption

    def activate(self, request: LearningActivationRequest) -> dict[str, Any]:
        self._validate_request(request)
        if request.intent not in {"inspect", "execute"}:
            raise LearningActivationError("unsupported activation intent")

        entry = self._resolve_registry_entry(request)
        decision = self._decision(request)
        if decision == "DENY":
            raise LearningActivationError("learned-skill activation denied")

        payload = self._snapshot(request, entry, decision)
        return payload

    def _validate_request(self, request: LearningActivationRequest) -> None:
        if not request.owner or len(request.owner) > 128 or _BLOCKED.search(request.owner):
            raise LearningActivationError("invalid owner")
        if not _SHA_RE.fullmatch(request.source_sha):
            raise LearningActivationError("invalid source SHA")
        if not request.correlation_id or len(request.correlation_id) > self.MAX_CORRELATION:
            raise LearningActivationError("invalid correlation id")
        if _BLOCKED.search(request.correlation_id) or _BLOCKED_VALUE.search(request.correlation_id):
            raise LearningActivationError("unsafe correlation id")
        if not _FP_RE.fullmatch(request.skill_fingerprint):
            raise LearningActivationError("invalid skill fingerprint")
        if request.h12_decision not in {"ALLOW_INSPECTION", "REQUIRE_APPROVAL", "DENY"}:
            raise LearningActivationError("invalid H12 decision")
        if request.approval_state not in {"NOT_REQUIRED", "PENDING", "APPROVED", "DENIED"}:
            raise LearningActivationError("invalid approval state")

    def _resolve_registry_entry(self, request: LearningActivationRequest) -> dict[str, Any]:
        snapshot = self._registry.snapshot()
        entries = snapshot.get("entries", [])
        for candidate in entries:
            if candidate.get("fingerprint") != request.skill_fingerprint:
                continue
            if candidate.get("owner") != request.owner:
                raise LearningActivationError("registry owner mismatch")
            if candidate.get("source_sha") != request.source_sha:
                raise LearningActivationError("registry source SHA mismatch")
            if candidate.get("correlation_id") != request.correlation_id:
                raise LearningActivationError("registry correlation mismatch")
            self._reject_unsafe(candidate)
            return json.loads(json.dumps(candidate, sort_keys=True))
        raise LearningActivationError("learned skill not found")

    def _decision(self, request: LearningActivationRequest) -> str:
        if request.intent == "inspect":
            if request.h12_decision != "ALLOW_INSPECTION":
                raise LearningActivationError("inspection requires H12 inspection decision")
            return "ALLOW_INSPECTION"

        if request.h12_decision == "DENY" or request.approval_state == "DENIED":
            return "DENY"
        if request.h12_decision != "REQUIRE_APPROVAL":
            raise LearningActivationError("execute activation requires H12 approval-required decision")
        if request.approval_state != "APPROVED":
            return "REQUIRE_APPROVAL"
        return "ALLOW_ACTIVATION"

    def _reject_unsafe(self, value: Any) -> None:
        if isinstance(value, dict):
            if len(value) > self.MAX_SKILL_KEYS:
                raise LearningActivationError("skill payload exceeds bounds")
            for key, item in value.items():
                if _BLOCKED.search(str(key)):
                    raise LearningActivationError("unsafe skill key")
                self._reject_unsafe(item)
        elif isinstance(value, list):
            if len(value) > self.MAX_SKILL_KEYS:
                raise LearningActivationError("skill list exceeds bounds")
            for item in value:
                self._reject_unsafe(item)
        elif isinstance(value, str) and (_BLOCKED_VALUE.search(value) or _BLOCKED.search(value)):
            raise LearningActivationError("unsafe skill value")

    def _snapshot(self, request: LearningActivationRequest, entry: dict[str, Any], decision: str) -> dict[str, Any]:
        skill = json.loads(json.dumps(entry, sort_keys=True))
        payload: dict[str, Any] = {
            "schema": "research-os-learning-activation/v1",
            "owner": request.owner,
            "source_sha": request.source_sha,
            "correlation_id": request.correlation_id,
            "skill_fingerprint": request.skill_fingerprint,
            "intent": request.intent,
            "h12_decision": request.h12_decision,
            "approval_state": request.approval_state,
            "decision": decision,
            "skill": skill,
            "read_only": True,
            "authority": "none",
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        payload["decision_fingerprint"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return json.loads(json.dumps(payload, sort_keys=True))
