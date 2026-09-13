from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any

_FP_RE = re.compile(r"^[0-9a-f]{64}$")
_BLOCKED = re.compile(
    r"(?:password|passwd|secret|token|api[_-]?key|credential|private[_-]?key|authorization|bearer|javascript:|data:text/html|powershell|cmd(?:\.exe)?|bash -c|os\.system|subprocess|shell|process|mcp|computer[_-]?use|release|merge|install|dispatch|bypass|approval|execute|executor)",
    re.I,
)


class LearnedSkillConsumptionError(ValueError):
    pass


@dataclass(frozen=True)
class LearnedSkillConsumptionRequest:
    owner: str
    skill_name: str
    expected_version: int
    registry_fingerprint: str
    correlation_id: str


class LearnedSkillConsumptionBoundary:
    """Prepare an approved learned skill for governed consumption without executing it."""

    MAX_KEYS = 64
    MAX_DEPTH = 8

    def prepare(
        self,
        request: LearnedSkillConsumptionRequest,
        registry_snapshot: tuple[dict[str, Any], ...],
    ) -> dict[str, Any]:
        self._validate_request(request)
        if not isinstance(registry_snapshot, tuple):
            raise LearnedSkillConsumptionError("registry snapshot must be immutable tuple")

        skill = next((item for item in registry_snapshot if item.get("name") == request.skill_name), None)
        if not isinstance(skill, dict):
            raise LearnedSkillConsumptionError("learned skill is not registered")
        if skill.get("status") != "approved":
            raise LearnedSkillConsumptionError("learned skill is not approved")
        if skill.get("version") != request.expected_version:
            raise LearnedSkillConsumptionError("learned skill version mismatch")

        self._scan(skill, 0)
        canonical_registry = json.dumps(registry_snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        actual_registry_fingerprint = hashlib.sha256(canonical_registry.encode("utf-8")).hexdigest()
        if actual_registry_fingerprint != request.registry_fingerprint:
            raise LearnedSkillConsumptionError("registry fingerprint mismatch")

        payload = {
            "schema": "research-os-learning-skill-consumption/v1",
            "owner": request.owner,
            "skill_name": request.skill_name,
            "skill_version": request.expected_version,
            "correlation_id": request.correlation_id,
            "registry_fingerprint": request.registry_fingerprint,
            "skill": json.loads(json.dumps(skill, sort_keys=True)),
            "consumption_state": "READY_FOR_GOVERNED_USE",
            "execution_authority": "H24",
            "read_only": True,
            "authority": "none",
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        payload["consumption_fingerprint"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return json.loads(json.dumps(payload, sort_keys=True))

    def _validate_request(self, request: LearnedSkillConsumptionRequest) -> None:
        if not request.owner or len(request.owner) > 128 or _BLOCKED.search(request.owner):
            raise LearnedSkillConsumptionError("invalid owner")
        if not request.skill_name or len(request.skill_name) > 128 or _BLOCKED.search(request.skill_name):
            raise LearnedSkillConsumptionError("invalid skill name")
        if not isinstance(request.expected_version, int) or isinstance(request.expected_version, bool) or not 1 <= request.expected_version <= 128:
            raise LearnedSkillConsumptionError("invalid skill version")
        if not _FP_RE.fullmatch(request.registry_fingerprint):
            raise LearnedSkillConsumptionError("invalid registry fingerprint")
        if not request.correlation_id or len(request.correlation_id) > 128 or _BLOCKED.search(request.correlation_id):
            raise LearnedSkillConsumptionError("invalid correlation id")

    def _scan(self, value: Any, depth: int) -> None:
        if depth > self.MAX_DEPTH:
            raise LearnedSkillConsumptionError("skill payload depth exceeds bounds")
        if isinstance(value, dict):
            if len(value) > self.MAX_KEYS:
                raise LearnedSkillConsumptionError("skill payload exceeds bounds")
            for key, item in value.items():
                if _BLOCKED.search(str(key)):
                    raise LearnedSkillConsumptionError("unsafe skill key")
                self._scan(item, depth + 1)
        elif isinstance(value, (list, tuple)):
            if len(value) > self.MAX_KEYS:
                raise LearnedSkillConsumptionError("skill payload exceeds bounds")
            for item in value:
                self._scan(item, depth + 1)
        elif isinstance(value, str) and _BLOCKED.search(value):
            raise LearnedSkillConsumptionError("unsafe skill value")
