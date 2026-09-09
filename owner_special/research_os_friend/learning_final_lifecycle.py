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
_ALLOWED_RESULTS = {"SUCCEEDED", "FAILED", "BLOCKED"}


class LearningFinalLifecycleError(ValueError):
    pass


@dataclass(frozen=True)
class LearningFinalLifecycleRequest:
    owner: str
    skill_name: str
    skill_version: int
    promotion_record_fingerprint: str
    correlation_id: str


class LearningFinalLifecycleBoundary:
    """Compose the completed learning lifecycle without granting new authority."""

    def finalize(
        self,
        request: LearningFinalLifecycleRequest,
        consumption: dict[str, Any],
        activation: dict[str, Any],
        executor_result: dict[str, Any],
        provenance: dict[str, Any],
    ) -> dict[str, Any]:
        self._validate_request(request)
        self._validate_envelopes(consumption, activation, executor_result, provenance)

        for value, fields in (
            (consumption, ("owner", "skill_name", "skill_version", "correlation_id")),
            (activation, ("owner", "skill_name", "skill_version")),
            (executor_result, ("owner", "skill_name", "skill_version", "correlation_id")),
            (provenance, ("owner", "skill_name", "skill_version", "correlation_id")),
        ):
            for field in fields:
                if getattr(request, field) != value.get(field):
                    raise LearningFinalLifecycleError(f"{field} mismatch")

        if activation.get("consumption_fingerprint") != consumption.get("consumption_fingerprint"):
            raise LearningFinalLifecycleError("activation is not bound to consumption")
        if executor_result.get("activation_fingerprint") != activation.get("activation_fingerprint"):
            raise LearningFinalLifecycleError("executor result is not bound to activation")
        if provenance.get("executor_result_fingerprint") != executor_result.get("executor_result_fingerprint"):
            raise LearningFinalLifecycleError("provenance is not bound to executor result")
        if not _FP_RE.fullmatch(request.promotion_record_fingerprint):
            raise LearningFinalLifecycleError("invalid promotion record fingerprint")

        status = executor_result["status"]
        if status == "SUCCEEDED":
            lifecycle_state = "LEARNING_LIFECYCLE_COMPLETE"
        elif status == "FAILED":
            lifecycle_state = "LEARNING_LIFECYCLE_FAILED"
        else:
            lifecycle_state = "LEARNING_LIFECYCLE_BLOCKED"

        payload = {
            "schema": "research-os-learning-final-lifecycle/v1",
            "owner": request.owner,
            "skill_name": request.skill_name,
            "skill_version": request.skill_version,
            "promotion_record_fingerprint": request.promotion_record_fingerprint,
            "correlation_id": request.correlation_id,
            "consumption_fingerprint": consumption["consumption_fingerprint"],
            "activation_fingerprint": activation["activation_fingerprint"],
            "executor_result_fingerprint": executor_result["executor_result_fingerprint"],
            "provenance_fingerprint": provenance["provenance_fingerprint"],
            "runtime_status": status,
            "lifecycle_state": lifecycle_state,
            "read_only": True,
            "authority": "none",
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        payload["lifecycle_fingerprint"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return json.loads(json.dumps(payload, sort_keys=True))

    def _validate_request(self, request: LearningFinalLifecycleRequest) -> None:
        if not request.owner or len(request.owner) > 128 or _BLOCKED.search(request.owner):
            raise LearningFinalLifecycleError("invalid owner")
        if not request.skill_name or len(request.skill_name) > 128 or _BLOCKED.search(request.skill_name):
            raise LearningFinalLifecycleError("invalid skill name")
        if not isinstance(request.skill_version, int) or isinstance(request.skill_version, bool) or not 1 <= request.skill_version <= 128:
            raise LearningFinalLifecycleError("invalid skill version")
        if not _FP_RE.fullmatch(request.promotion_record_fingerprint):
            raise LearningFinalLifecycleError("invalid promotion record fingerprint")
        if not request.correlation_id or len(request.correlation_id) > 128 or _BLOCKED.search(request.correlation_id):
            raise LearningFinalLifecycleError("invalid correlation id")

    def _validate_envelopes(self, consumption: Any, activation: Any, result: Any, provenance: Any) -> None:
        if not isinstance(consumption, dict) or consumption.get("schema") != "research-os-learning-skill-consumption/v1":
            raise LearningFinalLifecycleError("invalid consumption envelope")
        if not isinstance(activation, dict) or activation.get("schema") != "research-os-learning-skill-activation/v1":
            raise LearningFinalLifecycleError("invalid activation envelope")
        if not isinstance(result, dict) or result.get("schema") != "research-os-learning-executor-result/v1":
            raise LearningFinalLifecycleError("invalid executor result envelope")
        if not isinstance(provenance, dict) or provenance.get("schema") != "research-os-learning-evidence-provenance/v1":
            raise LearningFinalLifecycleError("invalid provenance envelope")
        for value in (consumption, activation, result, provenance):
            if value.get("read_only") is not True or value.get("authority") != "none":
                raise LearningFinalLifecycleError("authority contract violated")
        if result.get("status") not in _ALLOWED_RESULTS:
            raise LearningFinalLifecycleError("invalid runtime status")
        if provenance.get("evidence_state") != "BOUND_EXTERNAL_REFERENCES":
            raise LearningFinalLifecycleError("evidence provenance is incomplete")
