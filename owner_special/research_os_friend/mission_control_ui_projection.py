from __future__ import annotations

import copy
import json
import re
from collections.abc import Mapping
from typing import Any

from .mission_control_ui_schema import MissionControlUISchemaError, MissionControlUISchemaValidator
from .mission_control_unified_snapshot import MissionControlUnifiedSnapshot


class MissionControlUIProjectionError(ValueError):
    """Raised when the Phase 4I presentation adapter rejects unsafe input."""


class MissionControlUIProjection:
    """Pure, bounded adapter from the Phase 4H snapshot to a UI-safe view model."""

    SCHEMA = "research-os-mission-control-ui-projection/v1"
    MAX_BYTES = 64 * 1024
    MAX_STRING = 2048
    MAX_PANELS = 32
    MAX_ITEMS = 100
    MAX_DEPTH = 8
    REQUIRED_AUTHORITIES = MissionControlUnifiedSnapshot.AUTHORITIES
    PANEL_TYPES = MissionControlUISchemaValidator.PANEL_TYPES
    BLOCKED = re.compile(
        r"(?:bearer\s+|api[_-]?key|private.?key|password|credential|secret|token|"
        r"javascript:|data:text/html|subprocess|os\.system|child_process|"
        r"importlib|__import__|powershell|cmd\.exe|bash\s+-c|computer.?use|"
        r"mcp\s+(?:call|execute))", re.I
    )
    BLOCKED_KEYS = re.compile(
        r"(?:callback|callable|function|lambda|eval|exec|import|constructor|handler|"
        r"process|shell|command|browser|mcp|computer.?use|credential|secret|token|"
        r"private.?key|password|approval|permission|policy|register|mutation)", re.I
    )
    ALLOWED_PANEL_FIELDS = frozenset(
        {"id", "type", "title", "value", "items", "columns", "steps", "rows"}
    )

    def __init__(self, ui_validator: MissionControlUISchemaValidator | None = None) -> None:
        self._ui_validator = ui_validator or MissionControlUISchemaValidator()

    def project(self, snapshot: Mapping[str, Any], *, owner_id: str) -> dict[str, object]:
        self._validate_owner(owner_id)
        if not isinstance(snapshot, Mapping):
            raise MissionControlUIProjectionError("Phase 4H snapshot must be an object")
        source = copy.deepcopy(dict(snapshot))
        self._validate_snapshot(source, owner_id)

        ui_source = source.get("ui_schema")
        if not isinstance(ui_source, Mapping):
            raise MissionControlUIProjectionError("unified snapshot ui_schema is required")
        try:
            validated_ui = self._ui_validator.validate(ui_source, owner_id=owner_id)
        except MissionControlUISchemaError as exc:
            raise MissionControlUIProjectionError(f"invalid UI schema: {exc}") from exc

        result: dict[str, object] = {
            "schema": self.SCHEMA,
            "owner_id": owner_id,
            "read_only": True,
            **self.REQUIRED_AUTHORITIES,
            "source_snapshot": MissionControlUnifiedSnapshot.SCHEMA,
            "source_versions": copy.deepcopy(source["source_versions"]),
            "truncation": copy.deepcopy(source["truncation"]),
            "panels": self._normalize_panels(validated_ui["panels"]),
            "state_summary": self._state_summary(source),
        }
        self._validate_output(result, owner_id)
        return copy.deepcopy(result)

    def _validate_snapshot(self, snapshot: Mapping[str, Any], owner_id: str) -> None:
        if snapshot.get("schema") != MissionControlUnifiedSnapshot.SCHEMA:
            raise MissionControlUIProjectionError("unsupported Phase 4H snapshot schema/version")
        if snapshot.get("owner_id") != owner_id:
            raise MissionControlUIProjectionError("owner mismatch")
        if snapshot.get("read_only") is not True:
            raise MissionControlUIProjectionError("snapshot must be read-only")
        for field, expected in self.REQUIRED_AUTHORITIES.items():
            if snapshot.get(field) != expected:
                raise MissionControlUIProjectionError(f"invalid {field}")
        if not isinstance(snapshot.get("source_versions"), Mapping) or not isinstance(snapshot.get("truncation"), Mapping):
            raise MissionControlUIProjectionError("source metadata is malformed")
        self._walk_safe(snapshot)

    def _normalize_panels(self, panels: Any) -> list[dict[str, Any]]:
        if not isinstance(panels, list) or len(panels) > self.MAX_PANELS:
            raise MissionControlUIProjectionError("panels exceed presentation bounds")
        normalized: list[dict[str, Any]] = []
        seen: set[str] = set()
        for panel in panels:
            if not isinstance(panel, Mapping):
                raise MissionControlUIProjectionError("panel must be an object")
            if set(panel) - self.ALLOWED_PANEL_FIELDS:
                raise MissionControlUIProjectionError("panel contains unsupported fields")
            panel_id = panel.get("id")
            if not isinstance(panel_id, str) or not panel_id or panel.get("type") not in self.PANEL_TYPES:
                raise MissionControlUIProjectionError("invalid panel")
            if panel_id in seen:
                raise MissionControlUIProjectionError("duplicate panel id")
            seen.add(panel_id)
            item = {key: copy.deepcopy(panel[key]) for key in self.ALLOWED_PANEL_FIELDS if key in panel}
            for collection in ("items", "columns", "steps", "rows"):
                if collection in item and (not isinstance(item[collection], list) or len(item[collection]) > self.MAX_ITEMS):
                    raise MissionControlUIProjectionError(f"{collection} exceeds presentation bound")
            normalized.append(item)
        normalized.sort(key=lambda item: str(item["id"]))
        return normalized

    def _state_summary(self, snapshot: Mapping[str, Any]) -> dict[str, object]:
        gate = snapshot.get("gate_status")
        build = snapshot.get("build_identity")
        gate_status = gate.get("overall_status") if isinstance(gate, Mapping) else "UNKNOWN"
        build_status = build.get("status") if isinstance(build, Mapping) else "UNKNOWN"
        allowed_gate = {"PASSED", "FAILED", "PENDING", "UNKNOWN", "BLOCKED", "READY_FOR_FINAL_GATE"}
        allowed_build = {"VERIFIED", "INVALID", "CONFLICT", "STALE", "PENDING", "UNKNOWN"}
        return {
            "gate_status": gate_status if gate_status in allowed_gate else "UNKNOWN",
            "build_identity_status": build_status if build_status in allowed_build else "UNKNOWN",
            "read_only": True,
        }

    def _validate_output(self, payload: Mapping[str, Any], owner_id: str) -> None:
        if payload.get("schema") != self.SCHEMA or payload.get("owner_id") != owner_id:
            raise MissionControlUIProjectionError("invalid projection identity")
        if payload.get("read_only") is not True:
            raise MissionControlUIProjectionError("projection must remain read-only")
        for field, expected in self.REQUIRED_AUTHORITIES.items():
            if payload.get(field) != expected:
                raise MissionControlUIProjectionError(f"invalid {field}")
        if payload.get("source_snapshot") != MissionControlUnifiedSnapshot.SCHEMA:
            raise MissionControlUIProjectionError("invalid source snapshot reference")
        panels = payload.get("panels")
        if not isinstance(panels, list) or len(panels) > self.MAX_PANELS:
            raise MissionControlUIProjectionError("invalid panel collection")
        ids = [panel.get("id") for panel in panels if isinstance(panel, Mapping)]
        if ids != sorted(ids) or len(ids) != len(set(ids)):
            raise MissionControlUIProjectionError("panels must be unique and deterministically ordered")
        self._walk_safe(payload)
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        if len(encoded) > self.MAX_BYTES:
            raise MissionControlUIProjectionError("UI projection exceeds byte bound")

    def _walk_safe(self, value: Any, depth: int = 0) -> None:
        if depth > self.MAX_DEPTH:
            raise MissionControlUIProjectionError("payload nesting exceeds bound")
        if isinstance(value, Mapping):
            if len(value) > self.MAX_ITEMS:
                raise MissionControlUIProjectionError("mapping exceeds bound")
            for key, child in value.items():
                if not isinstance(key, str) or len(key) > self.MAX_STRING:
                    raise MissionControlUIProjectionError("invalid or oversized field name")
                if key not in self.REQUIRED_AUTHORITIES and self.BLOCKED_KEYS.search(key):
                    raise MissionControlUIProjectionError(f"blocked field: {key}")
                self._walk_safe(child, depth + 1)
        elif isinstance(value, list):
            if len(value) > self.MAX_ITEMS:
                raise MissionControlUIProjectionError("collection exceeds bound")
            for child in value:
                self._walk_safe(child, depth + 1)
        elif isinstance(value, (str, int, float, bool)) or value is None:
            if isinstance(value, str) and (len(value) > self.MAX_STRING or self.BLOCKED.search(value)):
                raise MissionControlUIProjectionError("blocked or oversized scalar")
        else:
            raise MissionControlUIProjectionError("unsupported dynamic value")

    def _validate_owner(self, owner_id: str) -> None:
        if not isinstance(owner_id, str) or not owner_id.strip() or len(owner_id) > self.MAX_STRING:
            raise MissionControlUIProjectionError("owner_id is invalid")
        if self.BLOCKED.search(owner_id):
            raise MissionControlUIProjectionError("owner_id is unsafe")
