#!/usr/bin/env python3
"""Bounded operating kernel for the native Research OS Control Center."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Mapping


MODES = {"LIVE", "SIMULATION", "DRY_RUN", "REPLAY"}
LIFECYCLE = (
    "INTENT",
    "VALIDATE",
    "AUTHORIZE",
    "EXECUTE",
    "OBSERVE",
    "EVIDENCE",
    "COMPLETE",
    "RECOVER",
)
HUMAN_REQUIRED = {"APPROVE", "AUTHORIZE", "RELEASE", "HIGH_RISK_ACTION"}


@dataclass(frozen=True)
class ControlCommand:
    command_id: str
    intent: str
    mode: str = "SIMULATION"
    risk: str = "LOW"
    target: str = ""
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.command_id.strip() or not self.intent.strip():
            raise ValueError("command identity and intent are required")
        if self.mode not in MODES:
            raise ValueError(f"unsupported mode: {self.mode}")
        if self.risk == "HIGH" and self.mode == "LIVE":
            raise ValueError("high-risk live execution requires human authorization")


@dataclass(frozen=True)
class ActivityEvent:
    event_id: str
    command_id: str
    state: str
    message: str
    evidence_ref: str | None = None


@dataclass(frozen=True)
class InspectorSnapshot:
    object_id: str
    object_type: str
    state: str
    owner: str
    version: str
    provenance: str | None
    evidence: tuple[str, ...]
    relations: tuple[str, ...]


class NativeControlCenter:
    """Pure bounded control model; adapters perform actual I/O."""

    def __init__(self, max_activity_items: int = 1000) -> None:
        if max_activity_items < 1:
            raise ValueError("max_activity_items must be positive")
        self.max_activity_items = max_activity_items
        self._activity: list[ActivityEvent] = []
        self._commands: dict[str, ControlCommand] = {}

    @staticmethod
    def fingerprint(command: ControlCommand) -> str:
        payload = {
            "command_id": command.command_id,
            "intent": command.intent,
            "mode": command.mode,
            "risk": command.risk,
            "target": command.target,
            "payload": dict(command.payload),
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    def prepare(self, command: ControlCommand) -> str:
        if command.command_id in self._commands:
            raise ValueError(f"duplicate command_id: {command.command_id}")
        self._commands[command.command_id] = command
        self._append(command.command_id, "INTENT", "Command prepared")
        self._append(command.command_id, "VALIDATE", "Command passed local structural validation")
        if command.mode in {"SIMULATION", "DRY_RUN", "REPLAY"}:
            self._append(command.command_id, "OBSERVE", f"Mode={command.mode}; no live execution performed")
        return self.fingerprint(command)

    def record_authorization(self, command_id: str, authorized: bool) -> None:
        command = self._require(command_id)
        if not authorized:
            self._append(command_id, "RECOVER", "Authorization denied; execution not performed")
            return
        if command.risk == "HIGH" and command.mode == "LIVE":
            self._append(command_id, "AUTHORIZE", "Human authorization recorded")
        else:
            self._append(command_id, "AUTHORIZE", "Authorization state recorded")

    def record_execution(self, command_id: str, success: bool, evidence_ref: str | None = None) -> None:
        command = self._require(command_id)
        if command.mode != "LIVE":
            raise ValueError("non-live command cannot be recorded as live execution")
        self._append(command_id, "EXECUTE", "Live execution observed")
        if success:
            self._append(command_id, "OBSERVE", "Execution completed successfully", evidence_ref)
            self._append(command_id, "EVIDENCE", "Execution evidence linked", evidence_ref)
            self._append(command_id, "COMPLETE", "Command completed", evidence_ref)
        else:
            self._append(command_id, "RECOVER", "Execution failed; recovery required", evidence_ref)

    def activity(self, limit: int = 100) -> tuple[ActivityEvent, ...]:
        if limit < 1:
            raise ValueError("limit must be positive")
        return tuple(self._activity[-min(limit, self.max_activity_items):])

    def inspector(
        self,
        object_id: str,
        object_type: str,
        state: str,
        owner: str,
        version: str,
        provenance: str | None = None,
        evidence: tuple[str, ...] = (),
        relations: tuple[str, ...] = (),
    ) -> InspectorSnapshot:
        if not object_id.strip() or not object_type.strip():
            raise ValueError("object identity and type are required")
        return InspectorSnapshot(
            object_id=object_id,
            object_type=object_type,
            state=state,
            owner=owner,
            version=version,
            provenance=provenance,
            evidence=tuple(evidence[:256]),
            relations=tuple(relations[:256]),
        )

    def human_required(self, action: str) -> bool:
        return action.upper() in HUMAN_REQUIRED

    def _require(self, command_id: str) -> ControlCommand:
        try:
            return self._commands[command_id]
        except KeyError as exc:
            raise KeyError(f"unknown command_id: {command_id}") from exc

    def _append(
        self,
        command_id: str,
        state: str,
        message: str,
        evidence_ref: str | None = None,
    ) -> None:
        if state not in LIFECYCLE:
            raise ValueError(f"invalid lifecycle state: {state}")
        event_id = f"EV-{len(self._activity) + 1:06d}"
        self._activity.append(
            ActivityEvent(
                event_id=event_id,
                command_id=command_id,
                state=state,
                message=message,
                evidence_ref=evidence_ref,
            )
        )
        if len(self._activity) > self.max_activity_items:
            del self._activity[: len(self._activity) - self.max_activity_items]
