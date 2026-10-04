"""Fail-closed Platform Adapter Runtime security gate.

This gate is intentionally authorization-only: it validates a server-derived
canonical session principal, an allowlisted capability/tool binding, and
bounded arguments before an existing executor is invoked. It never accepts
client role/owner overrides and never becomes a second executor.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from typing import Any, Mapping


class AdapterRuntimeDenied(PermissionError):
    """Raised when a request cannot cross the adapter runtime boundary."""


@dataclass(frozen=True)
class AdapterRuntimeDecision:
    allowed: bool
    request_id: str
    actor_user_id: str
    capability: str
    adapter: str
    reason: str
    evidence: dict[str, Any]


class AdapterRuntimeSecurityBoundary:
    """Validate an execution request immediately before adapter execution."""

    ALLOWED = {
        "web.fetch": "web",
        "github.repository": "github",
        "github.file": "github",
        "file.read": "file",
        "python.analyze": "python",
        "shell.run": "shell",
    }
    MAX_ARGUMENT_BYTES = 64 * 1024
    _ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
    _PATH_TRAVERSAL = re.compile(r"(?:^|[/\\])\.\.(?:[/\\]|$)|%2e%2e|%252e", re.I)

    def authorize(
        self,
        *,
        principal: Mapping[str, Any],
        capability: str,
        requested_tools: tuple[str, ...],
        arguments: Mapping[str, Any],
        request_id: str,
        policy_decision: str,
        now: int | None = None,
    ) -> AdapterRuntimeDecision:
        current = int(time.time() if now is None else now)
        actor = str(principal.get("user_id") or "").strip()
        session = str(principal.get("session_id") or "").strip()
        email = str(principal.get("email") or "").strip()
        if not actor or not session or not email:
            return self._deny(request_id, actor, capability, "missing_verified_session")
        role = str(principal.get("role") or "").strip().upper()
        if role not in {"OWNER", "USER"}:
            return self._deny(request_id, actor, capability, "invalid_server_role")
        exp = int(principal.get("exp") or 0)
        if exp <= current:
            return self._deny(request_id, actor, capability, "session_expired")
        if not self._ID_RE.fullmatch(request_id):
            return self._deny(request_id, actor, capability, "invalid_request_id")
        adapter = self.ALLOWED.get(capability)
        if adapter is None:
            return self._deny(request_id, actor, capability, "unknown_capability")
        if adapter not in requested_tools and capability not in requested_tools:
            return self._deny(request_id, actor, capability, "capability_not_explicitly_requested")
        if policy_decision != "ALLOW":
            return self._deny(request_id, actor, capability, "policy_not_allow")
        if not isinstance(arguments, Mapping):
            return self._deny(request_id, actor, capability, "invalid_arguments")
        try:
            encoded = json.dumps(arguments, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        except (TypeError, ValueError):
            return self._deny(request_id, actor, capability, "arguments_not_serializable")
        if len(encoded.encode("utf-8")) > self.MAX_ARGUMENT_BYTES:
            return self._deny(request_id, actor, capability, "arguments_too_large")
        if self._contains_traversal(arguments):
            return self._deny(request_id, actor, capability, "path_traversal")
        if capability == "shell.run" and not self._valid_shell(arguments):
            return self._deny(request_id, actor, capability, "shell_command_not_allowlisted")
        if capability == "python.analyze" and not isinstance(arguments.get("source"), str):
            return self._deny(request_id, actor, capability, "python_source_required")
        evidence = {
            "request_id": request_id,
            "actor": actor,
            "session_id": session,
            "capability": capability,
            "adapter": adapter,
            "policy_decision": "ALLOW",
            "authorization_result": "ALLOW",
            "arguments_fingerprint": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
            "timestamp": current,
            "result": "AUTHORIZED_FOR_ADAPTER",
        }
        return AdapterRuntimeDecision(True, request_id, actor, capability, adapter, "authorized", evidence)

    def enforce(self, **kwargs: Any) -> AdapterRuntimeDecision:
        decision = self.authorize(**kwargs)
        if not decision.allowed:
            raise AdapterRuntimeDenied(decision.reason)
        return decision

    def _deny(self, request_id: str, actor: str, capability: str, reason: str) -> AdapterRuntimeDecision:
        return AdapterRuntimeDecision(
            False,
            request_id,
            actor,
            capability,
            self.ALLOWED.get(capability, ""),
            reason,
            {
                "request_id": request_id,
                "actor": actor,
                "capability": capability,
                "authorization_result": "DENY",
                "reason": reason,
                "timestamp": int(time.time()),
                "result": "DENIED",
            },
        )

    @classmethod
    def _contains_traversal(cls, value: Any) -> bool:
        if isinstance(value, str):
            return bool(cls._PATH_TRAVERSAL.search(value))
        if isinstance(value, Mapping):
            return any(cls._contains_traversal(k) or cls._contains_traversal(v) for k, v in value.items())
        if isinstance(value, (list, tuple)):
            return any(cls._contains_traversal(item) for item in value)
        return False

    @staticmethod
    def _valid_shell(arguments: Mapping[str, Any]) -> bool:
        command = arguments.get("command")
        return (
            isinstance(command, list)
            and bool(command)
            and all(isinstance(item, str) and len(item) <= 4096 for item in command)
            and command[0] in {"python", "python3"}
        )


__all__ = ["AdapterRuntimeDenied", "AdapterRuntimeDecision", "AdapterRuntimeSecurityBoundary"]
