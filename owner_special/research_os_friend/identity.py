from __future__ import annotations

import re
from dataclasses import dataclass

_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def _safe_id(value: str, field: str) -> str:
    candidate = value.strip()
    if candidate in {"", ".", ".."} or not _ID_RE.fullmatch(candidate):
        raise ValueError(f"invalid {field}")
    return candidate


@dataclass(frozen=True)
class OwnerIdentity:
    owner_id: str
    display_name: str = "Owner"
    edition: str = "owner-special"

    def __post_init__(self) -> None:
        object.__setattr__(self, "owner_id", _safe_id(self.owner_id, "owner_id"))
        if not self.display_name.strip():
            raise ValueError("display_name is required")

    def matches(self, claimed_owner_id: str) -> bool:
        return self.owner_id == _safe_id(claimed_owner_id, "claimed_owner_id")
