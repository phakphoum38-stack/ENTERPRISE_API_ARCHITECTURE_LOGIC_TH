from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any


class MissionControlUISchemaError(ValueError):
    """Raised when a Mission Control presentation payload is unsafe or invalid."""


class MissionControlUISchemaValidator:
    """Strict, bounded validator for read-only Mission Control UI payloads.

    This is a presentation boundary only. It does not execute callbacks, tools,
    MCP actions, Computer Use actions, or mutate any runtime authority.
    """

    SCHEMA = "research-os-mission-control-ui/v1"
    MAX_BYTES = 64 * 1024
    MAX_PANELS = 32
    MAX_ITEMS = 100
    MAX_DEPTH = 8
    MAX_STRING = 2048
    AUTHORITIES = {
        "execution_authority": "FriendOrchestrator",
        "authorization_authority": "OwnerPolicy",
        "approval_authority": "ApprovalGate",
    }
    PANEL_TYPES = frozenset({"text", "metric", "status", "table", "timeline", "capability-health"})
    ALLOWED_ROOT = frozenset({"schema", "owner_id", "read_only", "execution_authority", "authorization_authority", "approval_authority", "panels"})
    ALLOWED_PANEL = frozenset({"id", "type", "title", "value", "items", "columns", "steps", "rows"})
    ALLOWED_SCALARS = (str, int, float, bool)
    BLOCKED_KEY = re.compile(r"(?:callback|callable|function|lambda|eval|exec|import|constructor|handler|process|shell|command|powershell|browser|mcp|computer.?use|credential|secret|token|private.?key|password|approval|permission|policy|register|mutation)", re.I)
    BLOCKED_VALUE = re.compile(r"(?:javascript:|data:text/html|subprocess|os\.system|child_process|importlib|__import__|powershell|cmd\.exe|bash\s+-c|computer.?use|mcp\s+(?:call|execute)|private.?key|bearer\s+|api[_-]?key)", re.I)

    def validate(self, payload: Mapping[str, Any], *, owner_id: str) -> dict[str, Any]:
        if not isinstance(payload, Mapping):
            raise MissionControlUISchemaError("payload must be a mapping")
        if not isinstance(owner_id, str) or not owner_id:
            raise MissionControlUISchemaError("owner_id is required")
        self._walk(payload, 0)
        if set(payload) != self.ALLOWED_ROOT:
            raise MissionControlUISchemaError("root fields must match the allow-list exactly")
        if payload.get("schema") != self.SCHEMA:
            raise MissionControlUISchemaError("unsupported schema/version")
        if payload.get("owner_id") != owner_id:
            raise MissionControlUISchemaError("owner mismatch")
        if payload.get("read_only") is not True:
            raise MissionControlUISchemaError("read_only=true is required")
        for field, expected in self.AUTHORITIES.items():
            if payload.get(field) != expected:
                raise MissionControlUISchemaError(f"invalid {field}")
        panels = payload.get("panels")
        if not isinstance(panels, list) or len(panels) > self.MAX_PANELS:
            raise MissionControlUISchemaError("panels must be a bounded list")
        ids: list[str] = []
        for panel in panels:
            if not isinstance(panel, Mapping) or set(panel) - self.ALLOWED_PANEL:
                raise MissionControlUISchemaError("panel contains unknown fields")
            if panel.get("type") not in self.PANEL_TYPES:
                raise MissionControlUISchemaError("unknown panel type")
            panel_id = panel.get("id")
            if not isinstance(panel_id, str) or not panel_id:
                raise MissionControlUISchemaError("panel id is required")
            ids.append(panel_id)
            for key in ("items", "columns", "steps", "rows"):
                if key in panel and isinstance(panel[key], list) and len(panel[key]) > self.MAX_ITEMS:
                    raise MissionControlUISchemaError(f"{key} exceeds bound")
        if ids != sorted(ids):
            raise MissionControlUISchemaError("panels must be deterministically ordered by id")
        return self._copy(payload)

    def _walk(self, value: Any, depth: int) -> None:
        if depth > self.MAX_DEPTH:
            raise MissionControlUISchemaError("payload nesting exceeds bound")
        if isinstance(value, Mapping):
            for key, child in value.items():
                if not isinstance(key, str) or len(key) > self.MAX_STRING:
                    raise MissionControlUISchemaError("invalid field name")
                if key not in self.AUTHORITIES and self.BLOCKED_KEY.search(key):
                    raise MissionControlUISchemaError(f"blocked field: {key}")
                self._walk(child, depth + 1)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            if len(value) > self.MAX_ITEMS:
                raise MissionControlUISchemaError("collection exceeds bound")
            for child in value:
                self._walk(child, depth + 1)
        elif isinstance(value, self.ALLOWED_SCALARS):
            if isinstance(value, str):
                if len(value) > self.MAX_STRING or self.BLOCKED_VALUE.search(value):
                    raise MissionControlUISchemaError("blocked or oversized scalar")
        else:
            raise MissionControlUISchemaError("unsupported dynamic value")

    def _copy(self, value: Any) -> Any:
        if isinstance(value, Mapping):
            return {key: self._copy(child) for key, child in value.items()}
        if isinstance(value, list):
            return [self._copy(child) for child in value]
        return value

    def validate_json_size(self, payload_bytes: bytes) -> None:
        if len(payload_bytes) > self.MAX_BYTES:
            raise MissionControlUISchemaError("payload exceeds byte bound")
