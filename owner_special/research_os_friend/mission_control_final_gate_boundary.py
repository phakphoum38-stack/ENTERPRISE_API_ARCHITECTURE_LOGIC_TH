from __future__ import annotations

import copy
import json
import re
from typing import Any, Mapping

from owner_special.research_os_friend.mission_control_final_gate_contract import (
    MissionControlFinalGateContract,
    MissionControlFinalGateContractError,
)


class MissionControlFinalGateBoundaryError(MissionControlFinalGateContractError):
    """Raised when readiness crosses the Final Gate boundary unsafely."""


class MissionControlFinalGateBoundary:
    """Fail-closed, read-only boundary hardening for the 4H readiness contract."""

    MAX_STRING = MissionControlFinalGateContract.MAX_STRING
    MAX_BYTES = MissionControlFinalGateContract.MAX_BYTES
    ACTION_FIELDS = MissionControlFinalGateContract.ACTION_FIELDS
    BLOCKED = re.compile(
        r"(?:bearer\s+|api[_-]?key|private.?key|password|credential|secret|token|"
        r"javascript:|subprocess|os\.system|child_process|powershell|cmd\.exe|bash\s+-c)",
        re.I,
    )
    SOURCE_AUTHORITY = "authoritative-ci-gate-evidence"

    def validate(self, *, readiness: Mapping[str, Any]) -> dict[str, object]:
        if not isinstance(readiness, Mapping):
            raise MissionControlFinalGateBoundaryError("readiness must be an object")
        copied = copy.deepcopy(dict(readiness))
        self._validate_boundary(copied)
        return MissionControlFinalGateContract().validate(readiness=copied)

    def _validate_boundary(self, payload: Mapping[str, Any]) -> None:
        if payload.get("source_authority") != self.SOURCE_AUTHORITY:
            raise MissionControlFinalGateBoundaryError("readiness source authority is invalid")
        for key, value in self._walk(payload):
            if isinstance(key, str) and key in self.ACTION_FIELDS:
                raise MissionControlFinalGateBoundaryError("action authority leaked into readiness")
            if isinstance(value, str) and (len(value) > self.MAX_STRING or self.BLOCKED.search(value)):
                raise MissionControlFinalGateBoundaryError("blocked or oversized readiness value")
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        if len(encoded) > self.MAX_BYTES:
            raise MissionControlFinalGateBoundaryError("readiness exceeds byte bound")

    def _walk(self, value: Any):
        if isinstance(value, Mapping):
            for key, item in value.items():
                yield key, item
                yield from self._walk(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                yield None, item
                yield from self._walk(item)
        else:
            yield None, value
