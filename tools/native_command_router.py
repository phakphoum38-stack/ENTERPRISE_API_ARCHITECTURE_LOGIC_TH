"""Bounded command routing for the canonical Native Control Center.

The router resolves a prepared command to an existing capability binding. It
does not execute work, grant authority, create a scheduler, or replace any
runtime. Execution remains owned by the referenced executor.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Mapping

from tools.control_center_capability_registry import CapabilityBinding, get_capability

MODES = frozenset({"LIVE", "SIMULATION", "DRY_RUN", "REPLAY"})
ACTION_CLASSES = frozenset({"READ_ONLY", "MUTATION"})
READ_ONLY_CAPABILITIES = frozenset({"control_center", "friend", "agent", "github", "factory_v3", "assurance"})

@dataclass(frozen=True)
class PreparedCommand:
    command_id: str
    capability_id: str
    action: str
    mode: str
    arguments: tuple[tuple[str, str], ...]
    action_class: str
    fingerprint: str

@dataclass(frozen=True)
class RouteDecision:
    command_id: str
    capability_id: str
    executor_ref: str
    mode: str
    executable: bool
    requires_human_authorization: bool
    reason: str

class NativeCommandRouter:
    """Prepare and route commands without executing them."""

    def prepare(self, *, capability_id: str, action: str, mode: str = "DRY_RUN",
                arguments: Mapping[str, str] | None = None,
                action_class: str = "READ_ONLY") -> PreparedCommand:
        if capability_id not in READ_ONLY_CAPABILITIES:
            raise ValueError(f"unsupported capability: {capability_id}")
        if mode not in MODES:
            raise ValueError(f"unsupported mode: {mode}")
        if action_class not in ACTION_CLASSES:
            raise ValueError(f"unsupported action class: {action_class}")
        action = action.strip()
        if not action or len(action) > 512:
            raise ValueError("action must be 1..512 characters")
        args = tuple(sorted((str(k), str(v)) for k, v in (arguments or {}).items()))
        if len(args) > 32:
            raise ValueError("too many arguments")
        binding = get_capability(capability_id)
        if not binding.executor_ref or binding.executor_ref == "UNKNOWN":
            raise ValueError("executor is not available")
        payload = {"capability_id": capability_id, "action": action, "mode": mode,
                   "arguments": args, "action_class": action_class,
                   "executor_ref": binding.executor_ref}
        fingerprint = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        return PreparedCommand(f"cmd-{fingerprint[:16]}", capability_id, action, mode, args, action_class, fingerprint)

    def route(self, command: PreparedCommand) -> RouteDecision:
        binding: CapabilityBinding = get_capability(command.capability_id)
        if command.mode in {"SIMULATION", "DRY_RUN", "REPLAY"}:
            return RouteDecision(command.command_id, command.capability_id, binding.executor_ref,
                                 command.mode, False, False, "non-executing mode")
        if command.action_class == "MUTATION":
            return RouteDecision(command.command_id, command.capability_id, binding.executor_ref,
                                 command.mode, False, True, "mutation requires external human authorization")
        return RouteDecision(command.command_id, command.capability_id, binding.executor_ref,
                             command.mode, True, False, "read-only command may be delegated to the existing executor")

__all__ = ["NativeCommandRouter", "PreparedCommand", "RouteDecision"]
