from __future__ import annotations

import copy
import json
import re
from typing import Any, Mapping


class MissionControlReleaseReadinessError(ValueError):
    """Raised when release-gate evidence cannot be projected safely."""


class MissionControlReleaseReadinessProjection:
    """Read-only summary of authoritative gate evidence; never grants release authority."""

    SCHEMA = "research-os-mission-control-release-readiness/v1"
    MAX_STRING = 2048
    MAX_BYTES = 16 * 1024
    BLOCKED = re.compile(
        r"(?:bearer\s+|api[_-]?key|private.?key|password|credential|secret|token|"
        r"javascript:|subprocess|os\.system|child_process|powershell|cmd\.exe|bash\s+-c)",
        re.I,
    )
    REQUIRED_GATES = (
        "architecture",
        "security_boundary",
        "generation",
        "external_tool",
        "api_contract",
        "e2e",
        "release",
    )
    ACTION_FIELDS = {"execute", "approve", "install", "dispatch", "release", "authorize"}

    def snapshot(
        self,
        *,
        owner_id: str,
        gate_evidence: Mapping[str, Mapping[str, Any]] | None,
        build_identity_status: str | None = None,
    ) -> dict[str, object]:
        if not isinstance(owner_id, str) or not owner_id.strip():
            raise MissionControlReleaseReadinessError("owner_id is required")
        if len(owner_id) > self.MAX_STRING or self.BLOCKED.search(owner_id):
            raise MissionControlReleaseReadinessError("owner_id is unsafe")
        if gate_evidence is None:
            gate_evidence = {}
        if not isinstance(gate_evidence, Mapping):
            raise MissionControlReleaseReadinessError("gate evidence must be an object")

        copied = copy.deepcopy(dict(gate_evidence))
        states: dict[str, str] = {}
        for gate in self.REQUIRED_GATES:
            evidence = copied.get(gate)
            if not isinstance(evidence, Mapping):
                states[gate] = "PENDING"
            elif evidence.get("passed") is True:
                states[gate] = "PASSED"
            elif evidence.get("passed") is False:
                states[gate] = "FAILED"
            else:
                states[gate] = "PENDING"

        if build_identity_status not in (None, "VERIFIED"):
            overall = "BLOCKED"
            reason = "build identity projection is not VERIFIED"
        elif any(state == "FAILED" for state in states.values()):
            overall = "BLOCKED"
            reason = "one or more required release gates failed"
        elif any(state != "PASSED" for state in states.values()):
            overall = "PENDING"
            reason = "one or more required release gates are not yet passed"
        else:
            overall = "READY_FOR_FINAL_GATE"
            reason = "all projected required gates passed; Final Gate remains authoritative"

        result: dict[str, object] = {
            "schema": self.SCHEMA,
            "owner_id": owner_id,
            "read_only": True,
            "source_authority": "authoritative-ci-gate-evidence",
            "overall_status": overall,
            "reason": reason,
            "build_identity_status": build_identity_status or "UNKNOWN",
            "gates": states,
            "authority_boundary": "projection-only; no release authority",
        }
        self._validate(result)
        return copy.deepcopy(result)

    def _validate(self, payload: Mapping[str, Any]) -> None:
        for value in self._walk_values(payload):
            if isinstance(value, str) and (len(value) > self.MAX_STRING or self.BLOCKED.search(value)):
                raise MissionControlReleaseReadinessError("blocked or oversized value")
        if payload.get("read_only") is not True:
            raise MissionControlReleaseReadinessError("projection must remain read-only")
        if self.ACTION_FIELDS.intersection(payload.keys()):
            raise MissionControlReleaseReadinessError("release action authority leaked into projection")
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        if len(encoded) > self.MAX_BYTES:
            raise MissionControlReleaseReadinessError("projection exceeds byte bound")

    def _walk_values(self, value: Any):
        if isinstance(value, Mapping):
            for key, item in value.items():
                if isinstance(key, str) and (len(key) > self.MAX_STRING or self.BLOCKED.search(key)):
                    raise MissionControlReleaseReadinessError("blocked or oversized key")
                yield from self._walk_values(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                yield from self._walk_values(item)
        else:
            yield value
