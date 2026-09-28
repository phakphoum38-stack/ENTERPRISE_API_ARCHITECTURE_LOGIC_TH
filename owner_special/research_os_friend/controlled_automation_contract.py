"""Policy-only safety boundary for future MCP, Computer Use, and automation."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse
from typing import Any


class AutomationDecision(str, Enum):
    ALLOW_READ_ONLY = "ALLOW_READ_ONLY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    DENY = "DENY"


class ControlledAutomationError(ValueError):
    """Raised when an automation request is malformed or unsafe."""


@dataclass(frozen=True)
class AutomationRequest:
    owner_id: str
    source_sha: str
    correlation_id: str
    capability: str
    action: str
    target: str
    side_effect: bool = False
    dry_run: bool = True


class ControlledAutomationContract:
    """Validate automation intent without executing or authorizing it."""

    SCHEMA = "research-os-controlled-automation/v1"
    MAX_TEXT = 2048
    SHA_RE = re.compile(r"^[0-9a-f]{40}$")
    CORRELATION_RE = re.compile(r"^[A-Za-z0-9._:-]{1,2048}$")
    CAPABILITIES = frozenset({"READ_WEB", "READ_FILE", "READ_MCP", "COMPUTER_USE_READ"})
    READ_ACTIONS = frozenset({"inspect", "fetch", "list", "observe", "snapshot"})
    BLOCKED_SCHEMES = frozenset({"javascript", "data", "file", "vbscript"})
    BLOCKED_PATTERNS = re.compile(
        r"(?:password|passwd|secret|token|api.?key|private.?key|credential|"
        r"shell|powershell|cmd\.exe|bash\s+-c|os\.system|subprocess|"
        r"eval|exec|mcp://|computer.?use|approve|release|merge|dispatch)",
        re.I,
    )

    def decide(self, request: AutomationRequest, *, allowed_hosts: tuple[str, ...] = (), allowed_roots: tuple[str, ...] = ()) -> dict[str, Any]:
        self._validate_request(request)
        target_kind = self._target_kind(request.target)
        if target_kind == "url":
            parsed = urlparse(request.target)
            if parsed.scheme.lower() in self.BLOCKED_SCHEMES or not parsed.hostname:
                return self._decision(request, AutomationDecision.DENY, "unsafe URL scheme or host")
            if allowed_hosts and parsed.hostname.lower() not in {host.lower() for host in allowed_hosts}:
                return self._decision(request, AutomationDecision.DENY, "target host is not allowlisted")
        elif target_kind == "path":
            if not allowed_roots or not any(request.target.startswith(root) for root in allowed_roots):
                return self._decision(request, AutomationDecision.DENY, "target path is not allowlisted")
        else:
            return self._decision(request, AutomationDecision.DENY, "unsupported target kind")

        if request.side_effect:
            return self._decision(request, AutomationDecision.REQUIRE_APPROVAL, "side effect requires explicit approval")
        if request.action not in self.READ_ACTIONS:
            return self._decision(request, AutomationDecision.DENY, "action is not read-only")
        return self._decision(request, AutomationDecision.ALLOW_READ_ONLY, "bounded read-only action")

    def _decision(self, request: AutomationRequest, decision: AutomationDecision, reason: str) -> dict[str, Any]:
        payload = {
            "schema": self.SCHEMA,
            "owner_id": request.owner_id,
            "source_sha": request.source_sha,
            "correlation_id": request.correlation_id,
            "capability": request.capability,
            "action": request.action,
            "decision": decision.value,
            "reason": reason,
            "dry_run": request.dry_run,
            "executor_authorized": False,
        }
        payload["decision_fingerprint"] = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return copy.deepcopy(payload)

    def _validate_request(self, request: AutomationRequest) -> None:
        if not isinstance(request, AutomationRequest):
            raise ControlledAutomationError("request must be AutomationRequest")
        self._validate_text(request.owner_id, "owner_id")
        if not self.SHA_RE.fullmatch(request.source_sha):
            raise ControlledAutomationError("source_sha must be an exact lowercase commit SHA")
        if not self.CORRELATION_RE.fullmatch(request.correlation_id):
            raise ControlledAutomationError("correlation_id is invalid")
        self._validate_text(request.capability, "capability")
        self._validate_text(request.action, "action")
        self._validate_text(request.target, "target")
        if request.capability not in self.CAPABILITIES:
            raise ControlledAutomationError("capability is not allowlisted")
        if self.BLOCKED_PATTERNS.search(request.target):
            raise ControlledAutomationError("target contains forbidden content")

    def _target_kind(self, target: str) -> str:
        parsed = urlparse(target)
        if parsed.scheme:
            return "url"
        if target.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", target):
            return "path"
        return "unknown"

    def _validate_text(self, value: str, name: str) -> None:
        if not isinstance(value, str) or not value or len(value) > self.MAX_TEXT:
            raise ControlledAutomationError(f"{name} is invalid or oversized")
