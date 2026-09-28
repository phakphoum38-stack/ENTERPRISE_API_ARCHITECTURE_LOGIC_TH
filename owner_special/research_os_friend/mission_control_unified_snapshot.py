from __future__ import annotations

import copy
import json
import re
from collections.abc import Mapping
from typing import Any

from .mission_control_ui_schema import MissionControlUISchemaError, MissionControlUISchemaValidator


class MissionControlUnifiedSnapshotError(ValueError):
    """Raised when a Phase 4H unified snapshot cannot be safely composed."""


class MissionControlUnifiedSnapshot:
    """Compose already-validated Mission Control projections into one read-only view.

    Phase 4H is an aggregation boundary only. It does not execute tools, call
    providers, authorize actions, approve releases, mutate runtime state, or
    create evidence. Every source must already be a bounded projection with
    the same owner scope and an explicit read-only boundary.
    """

    SCHEMA = "research-os-mission-control-unified-snapshot/v1"
    MAX_STRING = 2048
    MAX_BYTES = 64 * 1024
    MAX_RUNS = 100
    MAX_RECORDS = 100
    MAX_CAPABILITY_ROWS = 100
    MAX_DEPTH = 8
    SOURCE_SCHEMAS = {
        "trace": "research-os-mission-control/v1",
        "timeline": "research-os-mission-control-timeline/v1",
        "capabilities": "research-os-mission-control-capabilities/v1",
        "evidence": "research-os-mission-control-evidence/v1",
        "gate_status": "research-os-mission-control-release-readiness/v1",
        "build_identity": "research-os-mission-control-build-identity/v1",
    }
    AUTHORITIES = {
        "execution_authority": "FriendOrchestrator",
        "authorization_authority": "OwnerPolicy",
        "approval_authority": "ApprovalGate",
    }
    BLOCKED = re.compile(
        r"(?:bearer\s+|api[_-]?key|private.?key|password|credential|secret|token|"
        r"javascript:|data:text/html|subprocess|os\.system|child_process|"
        r"importlib|__import__|powershell|cmd\.exe|bash\s+-c|computer.?use|"
        r"mcp\s+(?:call|execute))",
        re.I,
    )
    BLOCKED_KEYS = re.compile(
        r"(?:callback|callable|function|lambda|eval|exec|import|constructor|handler|"
        r"process|shell|command|browser|mcp|computer.?use|credential|secret|token|"
        r"private.?key|password|approval|permission|policy|register|mutation)",
        re.I,
    )

    def __init__(self, ui_validator: MissionControlUISchemaValidator | None = None) -> None:
        self._ui_validator = ui_validator or MissionControlUISchemaValidator()

    def snapshot(
        self,
        *,
        owner_id: str,
        trace: Mapping[str, Any],
        timeline: Mapping[str, Any],
        capabilities: Mapping[str, Any],
        ui_schema: Mapping[str, Any],
        evidence: Mapping[str, Any],
        gate_status: Mapping[str, Any],
        build_identity: Mapping[str, Any] | None = None,
        run_limit: int = 100,
        evidence_limit: int = 100,
        capability_limit: int = 100,
    ) -> dict[str, object]:
        self._validate_owner(owner_id)
        self._validate_limit(run_limit, self.MAX_RUNS, "run_limit")
        self._validate_limit(evidence_limit, self.MAX_RECORDS, "evidence_limit")
        self._validate_limit(capability_limit, self.MAX_CAPABILITY_ROWS, "capability_limit")

        sources = {
            "trace": self._copy_source(trace),
            "timeline": self._copy_source(timeline),
            "capabilities": self._copy_source(capabilities),
            "ui_schema": copy.deepcopy(dict(ui_schema)) if isinstance(ui_schema, Mapping) else None,
            "evidence": self._copy_source(evidence),
            "gate_status": self._copy_source(gate_status),
            "build_identity": self._copy_source(build_identity) if build_identity is not None else None,
        }
        self._validate_sources(owner_id, sources)

        validated_ui = self._validate_ui_schema(sources["ui_schema"], owner_id)
        trace_view = self._bounded_trace(sources["trace"], run_limit)
        evidence_view = self._bounded_evidence(sources["evidence"], evidence_limit)
        capability_view = self._bounded_capabilities(sources["capabilities"], capability_limit)

        result: dict[str, object] = {
            "schema": self.SCHEMA,
            "owner_id": owner_id,
            "read_only": True,
            **self.AUTHORITIES,
            "source_versions": {
                "trace": self.SOURCE_SCHEMAS["trace"],
                "timeline": self.SOURCE_SCHEMAS["timeline"],
                "capabilities": self.SOURCE_SCHEMAS["capabilities"],
                "ui_schema": MissionControlUISchemaValidator.SCHEMA,
                "evidence": self.SOURCE_SCHEMAS["evidence"],
                "gate_status": self.SOURCE_SCHEMAS["gate_status"],
                "build_identity": self.SOURCE_SCHEMAS["build_identity"] if sources["build_identity"] is not None else None,
            },
            "truncation": {
                "runs": trace_view["truncated"],
                "evidence": evidence_view["truncated"],
                "capabilities": capability_view["truncated"],
            },
            "trace": trace_view["value"],
            "timeline": sources["timeline"],
            "capabilities": capability_view["value"],
            "ui_schema": validated_ui,
            "evidence": evidence_view["value"],
            "gate_status": sources["gate_status"],
            "build_identity": sources["build_identity"],
        }
        self._validate_output(result, owner_id)
        return copy.deepcopy(result)

    def _validate_sources(self, owner_id: str, sources: Mapping[str, Any]) -> None:
        for name in ("trace", "timeline", "capabilities", "evidence", "gate_status"):
            source = sources[name]
            if not isinstance(source, Mapping):
                raise MissionControlUnifiedSnapshotError(f"{name} projection must be an object")
            if source.get("schema") != self.SOURCE_SCHEMAS[name]:
                raise MissionControlUnifiedSnapshotError(f"unsupported {name} schema/version")
            if source.get("owner_id") != owner_id:
                raise MissionControlUnifiedSnapshotError(f"{name} owner mismatch")
            if source.get("read_only") is not True:
                raise MissionControlUnifiedSnapshotError(f"{name} must be read-only")
            for field, expected in self.AUTHORITIES.items():
                if field in source and source.get(field) != expected:
                    raise MissionControlUnifiedSnapshotError(f"invalid {name} {field}")

        build = sources["build_identity"]
        if build is not None:
            if build.get("schema") != self.SOURCE_SCHEMAS["build_identity"]:
                raise MissionControlUnifiedSnapshotError("unsupported build identity schema/version")
            if build.get("owner_id") != owner_id:
                raise MissionControlUnifiedSnapshotError("build identity owner mismatch")
            if build.get("read_only") is not True:
                raise MissionControlUnifiedSnapshotError("build identity must be read-only")
            for field, expected in self.AUTHORITIES.items():
                if field in build and build.get(field) != expected:
                    raise MissionControlUnifiedSnapshotError(f"invalid build identity {field}")

        self._walk_safe(sources)

    def _validate_ui_schema(self, ui_schema: Mapping[str, Any] | None, owner_id: str) -> dict[str, Any]:
        if ui_schema is None:
            raise MissionControlUnifiedSnapshotError("ui_schema projection is required")
        try:
            return self._ui_validator.validate(ui_schema, owner_id=owner_id)
        except MissionControlUISchemaError as exc:
            raise MissionControlUnifiedSnapshotError(f"invalid Phase 4D UI schema: {exc}") from exc

    def _bounded_trace(self, source: Mapping[str, Any], limit: int) -> dict[str, Any]:
        runs = source.get("runs")
        if not isinstance(runs, list):
            raise MissionControlUnifiedSnapshotError("trace runs must be a list")
        if not all(isinstance(item, Mapping) for item in runs):
            raise MissionControlUnifiedSnapshotError("trace runs must contain objects")
        ordered = sorted(runs, key=lambda item: str(item.get("run_id", "")))
        selected = ordered[:limit]
        value = copy.deepcopy(dict(source))
        value["runs"] = selected
        value["returned_runs"] = len(selected)
        value["truncated"] = len(runs) > len(selected)
        return {"value": value, "truncated": value["truncated"]}

    def _bounded_evidence(self, source: Mapping[str, Any], limit: int) -> dict[str, Any]:
        records = source.get("records")
        if not isinstance(records, list):
            raise MissionControlUnifiedSnapshotError("evidence records must be a list")
        if not all(isinstance(item, Mapping) for item in records):
            raise MissionControlUnifiedSnapshotError("evidence records must contain objects")
        ordered = sorted(records, key=lambda item: str(item.get("run_id", "")))
        selected = ordered[:limit]
        value = copy.deepcopy(dict(source))
        value["records"] = selected
        value["returned_records"] = len(selected)
        value["truncated"] = len(records) > len(selected)
        return {"value": value, "truncated": value["truncated"]}

    def _bounded_capabilities(self, source: Mapping[str, Any], limit: int) -> dict[str, Any]:
        rows = source.get("rows")
        if not isinstance(rows, list):
            raise MissionControlUnifiedSnapshotError("capability rows must be a list")
        if not all(isinstance(item, Mapping) for item in rows):
            raise MissionControlUnifiedSnapshotError("capability rows must contain objects")
        ordered = sorted(rows, key=lambda item: str(item.get("name", "")))
        selected = ordered[:limit]
        value = copy.deepcopy(dict(source))
        value["rows"] = selected
        value["returned"] = len(selected)
        value["truncated"] = len(rows) > len(selected)
        return {"value": value, "truncated": value["truncated"]}

    def _validate_output(self, payload: Mapping[str, Any], owner_id: str) -> None:
        if payload.get("schema") != self.SCHEMA:
            raise MissionControlUnifiedSnapshotError("invalid unified snapshot schema/version")
        if payload.get("owner_id") != owner_id or payload.get("read_only") is not True:
            raise MissionControlUnifiedSnapshotError("unified snapshot authority boundary is invalid")
        for field, expected in self.AUTHORITIES.items():
            if payload.get(field) != expected:
                raise MissionControlUnifiedSnapshotError(f"invalid {field}")
        self._walk_safe(payload)
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        if len(encoded) > self.MAX_BYTES:
            raise MissionControlUnifiedSnapshotError("unified snapshot exceeds byte bound")

    def _walk_safe(self, value: Any, depth: int = 0) -> None:
        if depth > self.MAX_DEPTH:
            raise MissionControlUnifiedSnapshotError("payload nesting exceeds bound")
        if isinstance(value, Mapping):
            if len(value) > self.MAX_RECORDS:
                raise MissionControlUnifiedSnapshotError("mapping exceeds bound")
            for key, child in value.items():
                if not isinstance(key, str) or len(key) > self.MAX_STRING:
                    raise MissionControlUnifiedSnapshotError("invalid or oversized field name")
                if key not in self.AUTHORITIES and self.BLOCKED_KEYS.search(key):
                    raise MissionControlUnifiedSnapshotError(f"blocked field: {key}")
                self._walk_safe(child, depth + 1)
        elif isinstance(value, list):
            if len(value) > self.MAX_RECORDS:
                raise MissionControlUnifiedSnapshotError("collection exceeds bound")
            for child in value:
                self._walk_safe(child, depth + 1)
        elif isinstance(value, (str, int, float, bool)) or value is None:
            if isinstance(value, str) and (len(value) > self.MAX_STRING or self.BLOCKED.search(value)):
                raise MissionControlUnifiedSnapshotError("blocked or oversized scalar")
        else:
            raise MissionControlUnifiedSnapshotError("unsupported dynamic value")

    @staticmethod
    def _copy_source(value: Mapping[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return None
        if not isinstance(value, Mapping):
            raise MissionControlUnifiedSnapshotError("projection must be an object")
        return copy.deepcopy(dict(value))

    def _validate_owner(self, owner_id: str) -> None:
        if not isinstance(owner_id, str) or not owner_id.strip():
            raise MissionControlUnifiedSnapshotError("owner_id is required")
        if len(owner_id) > self.MAX_STRING or self.BLOCKED.search(owner_id):
            raise MissionControlUnifiedSnapshotError("owner_id is unsafe")

    @staticmethod
    def _validate_limit(value: int, maximum: int, name: str) -> None:
        if not isinstance(value, int) or isinstance(value, bool) or value < 1 or value > maximum:
            raise MissionControlUnifiedSnapshotError(f"{name} must be between 1 and {maximum}")
