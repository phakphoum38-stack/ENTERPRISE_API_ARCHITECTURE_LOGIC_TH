"""Read-only boundary for consuming verified learned-skill registry entries."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Mapping

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_FP_RE = re.compile(r"^[0-9a-f]{64}$")
_BLOCKED = re.compile(r"(?:secret|token|password|private.?key|api.?key|credential|approval|authorize|release|merge|dispatch|shell|process|subprocess|mcp|computer.?use|exec|eval)", re.I)
_BLOCKED_VALUE = re.compile(r"(?:BEGIN [A-Z ]*PRIVATE KEY|gh[pousr]_|sk-proj-|javascript:|data:text/html|powershell|cmd(?:\.exe)?|bash -c|os\.system|subprocess)", re.I)


class LearningConsumptionError(ValueError):
    """Raised when a learned-skill consumption request is unsafe or mismatched."""


@dataclass(frozen=True)
class LearningConsumptionRequest:
    owner: str
    source_sha: str
    correlation_id: str
    skill_fingerprint: str
    intent: str = "inspect"

    def __post_init__(self) -> None:
        if not isinstance(self.owner, str) or not self.owner or len(self.owner) > 256:
            raise LearningConsumptionError("owner must be bounded")
        if not isinstance(self.source_sha, str) or not _SHA_RE.fullmatch(self.source_sha):
            raise LearningConsumptionError("invalid source SHA")
        if not isinstance(self.correlation_id, str) or not self.correlation_id or len(self.correlation_id) > 256 or _BLOCKED.search(self.correlation_id):
            raise LearningConsumptionError("unsafe correlation id")
        if not isinstance(self.skill_fingerprint, str) or not _FP_RE.fullmatch(self.skill_fingerprint):
            raise LearningConsumptionError("invalid skill fingerprint")
        if self.intent not in {"inspect", "execute"}:
            raise LearningConsumptionError("invalid consumption intent")


class LearningSkillConsumer:
    """Resolve registry entries without granting execution authority."""

    def __init__(self, registry: Any) -> None:
        self._registry = registry

    def inspect(self, request: LearningConsumptionRequest) -> dict[str, Any]:
        entry = self._resolve(request)
        return self._snapshot(entry, request, decision="ALLOW_INSPECTION")

    def decide(self, request: LearningConsumptionRequest) -> dict[str, Any]:
        entry = self._resolve(request)
        decision = "REQUIRE_APPROVAL" if request.intent == "execute" else "ALLOW_INSPECTION"
        return self._snapshot(entry, request, decision=decision)

    def _resolve(self, request: LearningConsumptionRequest) -> Any:
        entries = self._registry.snapshot().get("entries", [])
        for entry in entries:
            if entry.get("fingerprint") != request.skill_fingerprint:
                continue
            if entry.get("owner") != request.owner or entry.get("source_sha") != request.source_sha or entry.get("correlation_id") != request.correlation_id:
                raise LearningConsumptionError("registry identity mismatch")
            for value in entry.values():
                if isinstance(value, str) and (_BLOCKED.search(value) or _BLOCKED_VALUE.search(value)):
                    raise LearningConsumptionError("unsafe registry content")
            return entry
        raise LearningConsumptionError("learned skill not found")

    @staticmethod
    def _snapshot(entry: Mapping[str, Any], request: LearningConsumptionRequest, *, decision: str) -> dict[str, Any]:
        material = {
            "owner": request.owner,
            "source_sha": request.source_sha,
            "correlation_id": request.correlation_id,
            "skill_fingerprint": request.skill_fingerprint,
            "intent": request.intent,
            "decision": decision,
        }
        return {
            "schema": "research-os-learning-consumption/v1",
            "owner": request.owner,
            "source_sha": request.source_sha,
            "correlation_id": request.correlation_id,
            "skill": dict(entry),
            "intent": request.intent,
            "decision": decision,
            "read_only": True,
            "authority": "none",
            "decision_fingerprint": hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        }
