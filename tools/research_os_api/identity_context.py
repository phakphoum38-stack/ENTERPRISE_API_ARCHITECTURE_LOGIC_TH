"""Trusted identity context for Research OS -> Friend requests."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

from api_auth import require_session

_SAFE_SCOPE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")


@dataclass(frozen=True)
class IdentityContext:
    """Server-derived identity used for Friend, memory, and workspace scoping."""

    user_id: str
    role: str
    session_id: str
    profile_id: str

    def friend_headers(self) -> dict[str, str]:
        return {
            "X-Research-OS-Owner": self.user_id,
            "X-Research-OS-Profile": self.profile_id,
            "X-Research-OS-Session": self.session_id,
        }


def _scope(value: Any, name: str) -> str:
    text = str(value or "").strip()
    if not text or not _SAFE_SCOPE.fullmatch(text):
        raise ValueError(f"invalid {name}")
    return text


def resolve_identity_context(headers: Mapping[str, str]) -> IdentityContext:
    """Resolve identity exclusively from the verified Research OS session."""
    principal = require_session(headers)
    user_id = _scope(principal.get("user_id"), "user_id")
    role = _scope(principal.get("role") or "user", "role").lower()
    session_id = _scope(principal.get("session_id"), "session_id")
    profile_id = f"user-{user_id}"
    return IdentityContext(user_id, role, session_id, profile_id)
