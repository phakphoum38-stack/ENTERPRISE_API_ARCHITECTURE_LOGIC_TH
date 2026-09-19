"""Canonical Phase 6B controlled action intent boundary.

This module validates immutable, owner/session-bound action intent. It does not
authorize, approve, execute, or emit evidence for an action.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ActionIntentError(ValueError):
    """Raised when an action intent is malformed or unsafe."""


class ActionEffect(str, Enum):
    READ_ONLY = "read_only"
    SIDE_EFFECT = "side_effect"


class ActionApproval(str, Enum):
    NOT_REQUIRED = "not_required"
    REQUIRED = "required"


_ALLOWED_ACTIONS = frozenset({
    "inspect",
    "fetch",
    "list",
    "observe",
    "snapshot",
})
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_BLOCKED = re.compile(
    r"(?:^|[^a-z])(shell|powershell|cmd(?:\.exe)?|bash|subprocess|os\.system|"
    r"exec|eval|callback|lambda|dynamic import|mcp://|computer.?use|"
    r"javascript:|data:text/html|credential|password|passwd|secret|token|"
    r"api.?key|private.?key|approve|authorize|release|merge|dispatch)(?:$|[^a-z])",
    re.IGNORECASE,
)
_BLOCKED_SCHEME = re.compile(r"(?:(?:javascript|data)\\s*:)", re.IGNORECASE)


@dataclass(frozen=True)
class ActionIntent:
    schema: str
    version: int
    owner_id: str
    session_id: str
    intent_id: str
    action_type: str
    goal: str
    target: str
    effect: ActionEffect
    approval: ActionApproval
    correlation_id: str
    source_sha: str
    params: tuple[tuple[str, str], ...] = ()

    SCHEMA = "research-os-action-intent"
    VERSION = 1
    MAX_TEXT = 2048
    MAX_PARAMS = 32

    def __post_init__(self) -> None:
        ActionIntentValidator.validate(self)

    @property
    def request_fingerprint(self) -> str:
        payload = self.canonical_payload()
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "version": self.version,
            "owner_id": self.owner_id,
            "session_id": self.session_id,
            "intent_id": self.intent_id,
            "action_type": self.action_type,
            "goal": self.goal,
            "target": self.target,
            "effect": self.effect.value,
            "approval": self.approval.value,
            "correlation_id": self.correlation_id,
            "source_sha": self.source_sha,
            "params": [[key, value] for key, value in self.params],
        }

    def to_dict(self) -> dict[str, Any]:
        return dict(self.canonical_payload())


class ActionIntentValidator:
    """Pure validation boundary; never calls policy, approval, or execution."""

    @classmethod
    def validate(cls, intent: ActionIntent) -> None:
        if not isinstance(intent, ActionIntent):
            raise ActionIntentError("intent must be ActionIntent")
        if intent.schema != ActionIntent.SCHEMA or intent.version != ActionIntent.VERSION:
            raise ActionIntentError("unsupported action intent schema or version")
        cls._text(intent.owner_id, "owner_id", identifier=True)
        cls._text(intent.session_id, "session_id", identifier=True)
        cls._text(intent.intent_id, "intent_id", identifier=True)
        cls._text(intent.correlation_id, "correlation_id", identifier=True)
        cls._text(intent.action_type, "action_type")
        cls._text(intent.goal, "goal")
        cls._text(intent.target, "target")
        if not _SHA_RE.fullmatch(intent.source_sha):
            raise ActionIntentError("source_sha must be an exact lowercase commit SHA")
        if intent.action_type not in _ALLOWED_ACTIONS:
            raise ActionIntentError("action_type is not allowlisted")
        if intent.effect is not ActionEffect.READ_ONLY:
            raise ActionIntentError("Phase 6B permits only bounded read-only intents")
        if intent.approval is not ActionApproval.NOT_REQUIRED:
            raise ActionIntentError("read-only intents cannot claim an approval state")
        if len(intent.params) > ActionIntent.MAX_PARAMS:
            raise ActionIntentError("too many action parameters")
        seen: set[str] = set()
        for key, value in intent.params:
            cls._text(key, "parameter key", identifier=True)
            cls._text(value, "parameter value")
            if key in seen:
                raise ActionIntentError("duplicate action parameter")
            seen.add(key)
        serialized = json.dumps(intent.canonical_payload(), sort_keys=True, separators=(",", ":"))
        if len(serialized.encode("utf-8")) > 64 * 1024:
            raise ActionIntentError("action intent exceeds byte bound")
        for field_name, value in (
            ("goal", intent.goal),
            ("target", intent.target),
            *(("parameter", value) for _, value in intent.params),
        ):
            if _BLOCKED.search(value) or _BLOCKED_SCHEME.search(value):
                raise ActionIntentError(f"{field_name} contains forbidden executable or credential-like content")

    @staticmethod
    def _text(value: str, name: str, *, identifier: bool = False) -> None:
        if not isinstance(value, str) or not value or len(value) > ActionIntent.MAX_TEXT:
            raise ActionIntentError(f"{name} is invalid or oversized")
        if identifier and not _ID_RE.fullmatch(value):
            raise ActionIntentError(f"{name} is invalid")
