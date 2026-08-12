from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass

_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def _validate_identifier(value: str, *, field: str) -> str:
    candidate = value.strip()
    if not candidate:
        raise ValueError(f"{field} is required")
    if candidate in {".", ".."} or not _ID_PATTERN.fullmatch(candidate):
        raise ValueError(
            f"{field} must be 1-64 characters using letters, numbers, '.', '_' or '-'"
        )
    return candidate


def safe_local_user_id(raw: str) -> str:
    """Return a deterministic storage-safe ID for a local OS account name."""
    candidate = raw.strip()
    if _ID_PATTERN.fullmatch(candidate) and candidate not in {".", ".."}:
        return candidate
    digest = hashlib.sha256(candidate.encode("utf-8")).hexdigest()[:20]
    return f"user-{digest}"


@dataclass(frozen=True)
class UserContext:
    """Validated local user/profile scope for all mutable per-user data."""

    user_id: str
    profile_id: str = "default"

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "user_id", _validate_identifier(self.user_id, field="user_id")
        )
        object.__setattr__(
            self,
            "profile_id",
            _validate_identifier(self.profile_id, field="profile_id"),
        )

    @property
    def scope_key(self) -> str:
        return f"{self.user_id}/{self.profile_id}"

    @classmethod
    def from_environment(cls) -> "UserContext":
        raw_user = (
            os.environ.get("RESEARCH_OS_V3_USER_ID")
            or os.environ.get("USERNAME")
            or os.environ.get("USER")
            or "local-user"
        )
        profile_id = os.environ.get("RESEARCH_OS_V3_PROFILE_ID", "default")
        return cls(user_id=safe_local_user_id(raw_user), profile_id=profile_id)
