from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryItem:
    owner_id: str
    profile_id: str
    session_id: str
    kind: str
    text: str


class ScopedMemory:
    """Owner/profile/session scoped memory with no implicit cross-scope reads."""

    def __init__(self) -> None:
        self._items: list[MemoryItem] = []

    def remember(
        self,
        *,
        owner_id: str,
        profile_id: str,
        session_id: str,
        kind: str,
        text: str,
    ) -> None:
        self._items.append(MemoryItem(owner_id, profile_id, session_id, kind, text))

    def recall(self, *, owner_id: str, profile_id: str, session_id: str) -> tuple[MemoryItem, ...]:
        return tuple(
            item
            for item in self._items
            if item.owner_id == owner_id
            and item.profile_id == profile_id
            and item.session_id == session_id
        )
