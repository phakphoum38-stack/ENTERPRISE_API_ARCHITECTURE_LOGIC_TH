from __future__ import annotations

import copy
import json
import re
from typing import Any, Mapping


class MissionControlFinalGateContractError(ValueError):
    """Raised when a Mission Control readiness projection is not valid Final Gate input."""


class MissionControlFinalGateContract:
    """Read-only contract checker between Mission Control readiness and the Final Gate."""

    SCHEMA = "research-os-mission-control-final-gate-contract/v1"
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
    MAX_STRING = 2048
    MAX_BYTES = 16 * 1024
    BLOCKED = re.compile(
        r"(?:bearer\s+|api[_-]?key|private.?key|password|credential|secret|token|"
        r"javascript:|subprocess|os\.system|child_process|powershell|cmd\.exe|bash\s+-c)",
        re.I,
    )

    def validate(self, *, readiness: Mapping[str, Any]) -> dict[str, object]:
        if not isinstance(readiness, Mapping):
            raise MissionControlFinalGateContractError("readiness must be an object")
        copied = copy.deepcopy(dict(readiness))
        self._validate_input(copied)

        if copied.get("schema") != "research-os-mission-control-release-readiness/v1":
            raise MissionControlFinalGateContractError("unsupported readiness schema")
        if copied.get("read_only") is not True:
            raise MissionControlFinalGateContractError("readiness must remain read-only")
        if copied.get("build_identity_status") != "VERIFIED":
            raise MissionControlFinalGateContractError("build identity is not VERIFIED")
        if copied.get("overall_status") != "READY_FOR_FINAL_GATE":
            raise MissionControlFinalGateContractError("readiness is not READY_FOR_FINAL_GATE")
        if copied.get("authority_boundary") != "projection-only; no release authority":
            raise MissionControlFinalGateContractError("release authority boundary is invalid")

        gates = copied.get("gates")
        if not isinstance(gates, Mapping):
            raise MissionControlFinalGateContractError("gates must be an object")
        if set(gates) != set(self.REQUIRED_GATES):
            raise MissionControlFinalGateContractError("required gate set is incomplete or unexpected")
        if any(gates[gate] != "PASSED" for gate in self.REQUIRED_GATES):
            raise MissionControlFinalGateContractError("all required gates must be PASSED")

        result: dict[str, object] = {
            "schema": self.SCHEMA,
            "owner_id": copied["owner_id"],
            "input_status": "READY_FOR_FINAL_GATE",
            "build_identity_status": "VERIFIED",
            "required_gates": list(self.REQUIRED_GATES),
            "read_only": True,
            "authority_boundary": "contract-only; Final Gate remains authoritative",
        }
        self._validate_output(result)
        return copy.deepcopy(result)

    def _validate_input(self, payload: Mapping[str, Any]) -> None:
        for value in self._walk_values(payload):
            if isinstance(value, str) and (len(value) > self.MAX_STRING or self.BLOCKED.search(value)):
                raise MissionControlFinalGateContractError("blocked or oversized readiness value")
        if self.ACTION_FIELDS.intersection(payload.keys()):
            raise MissionControlFinalGateContractError("release action authority leaked into readiness")
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        if len(encoded) > self.MAX_BYTES:
            raise MissionControlFinalGateContractError("readiness exceeds byte bound")

    def _validate_output(self, payload: Mapping[str, Any]) -> None:
        for value in self._walk_values(payload):
            if isinstance(value, str) and (len(value) > self.MAX_STRING or self.BLOCKED.search(value)):
                raise MissionControlFinalGateContractError("blocked or oversized contract value")
        if self.ACTION_FIELDS.intersection(payload.keys()):
            raise MissionControlFinalGateContractError("release action authority leaked into contract")
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        if len(encoded) > self.MAX_BYTES:
            raise MissionControlFinalGateContractError("contract exceeds byte bound")

    def _walk_values(self, value: Any):
        if isinstance(value, Mapping):
            for key, item in value.items():
                if isinstance(key, str) and (len(key) > self.MAX_STRING or self.BLOCKED.search(key)):
                    raise MissionControlFinalGateContractError("blocked or oversized key")
                yield from self._walk_values(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                yield from self._walk_values(item)
        else:
            yield value
