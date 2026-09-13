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


class LearnedSkillActivationError(ValueError):
    pass


@dataclass(frozen=True)
class LearnedSkillActivationRequest:
    owner: str
    skill_name: str
    skill_version: int
    consumption_fingerprint: str
    activation_id: str


class LearnedSkillActivationBoundary:
    """Issue a bounded activation envelope; execution remains a downstream concern."""

    def activate(
        self,
        request: LearnedSkillActivationRequest,
        consumption: dict[str, Any],
    ) -> dict[str, Any]:
        self._validate_request(request)
        self._validate_consumption(consumption)
        for field in ("owner", "skill_name", "skill_version", "consumption_fingerprint"):
            if getattr(request, field) != consumption.get(field):
                raise LearnedSkillActivationError(f"consumption {field} mismatch")

        skill = consumption["skill"]
        self._scan(skill, 0)
        payload = {
            "schema": "research-os-learning-skill-activation/v1",
            "activation_id": request.activation_id,
            "owner": request.owner,
            "skill_name": request.skill_name,
            "skill_version": request.skill_version,
            "consumption_fingerprint": request.consumption_fingerprint,
            "skill": json.loads(json.dumps(skill, sort_keys=True)),
            "activation_state": "READY_FOR_H25",
            "execution_authority": "H25",
            "read_only": True,
            "authority": "none",
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        payload["activation_fingerprint"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return json.loads(json.dumps(payload, sort_keys=True))

    def _validate_request(self, request: LearnedSkillActivationRequest) -> None:
        if not request.owner or len(request.owner) > 128 or _BLOCKED.search(request.owner):
            raise LearnedSkillActivationError("invalid owner")
        if not request.skill_name or len(request.skill_name) > 128 or _BLOCKED.search(request.skill_name):
            raise LearnedSkillActivationError("invalid skill name")
        if not isinstance(request.skill_version, int) or isinstance(request.skill_version, bool) or not 1 <= request.skill_version <= 128:
            raise LearnedSkillActivationError("invalid skill version")
        if not _FP_RE.fullmatch(request.consumption_fingerprint):
            raise LearnedSkillActivationError("invalid consumption fingerprint")
        if not request.activation_id or len(request.activation_id) > 128 or _BLOCKED.search(request.activation_id):
            raise LearnedSkillActivationError("invalid activation id")

    def _validate_consumption(self, value: Any) -> None:
        if not isinstance(value, dict) or value.get("schema") != "research-os-learning-skill-consumption/v1":
            raise LearnedSkillActivationError("invalid consumption envelope")
        if value.get("consumption_state") != "READY_FOR_GOVERNED_USE":
            raise LearnedSkillActivationError("consumption is not ready")
        if value.get("read_only") is not True or value.get("authority") != "none":
            raise LearnedSkillActivationError("consumption authority contract violated")
        if value.get("execution_authority") != "H24":
            raise LearnedSkillActivationError("invalid activation authority")
        if not isinstance(value.get("skill"), dict):
            raise LearnedSkillActivationError("missing skill payload")

    def _scan(self, value: Any, depth: int) -> None:
        if depth > 8:
            raise LearnedSkillActivationError("skill payload depth exceeds bounds")
        if isinstance(value, dict):
            if len(value) > 64:
                raise LearnedSkillActivationError("skill payload exceeds bounds")
            for key, item in value.items():
                if _BLOCKED.search(str(key)):
                    raise LearnedSkillActivationError("unsafe skill key")
                self._scan(item, depth + 1)
        elif isinstance(value, (list, tuple)):
            if len(value) > 64:
                raise LearnedSkillActivationError("skill payload exceeds bounds")
            for item in value:
                self._scan(item, depth + 1)
        elif isinstance(value, str) and _BLOCKED.search(value):
            raise LearnedSkillActivationError("unsafe skill value")
