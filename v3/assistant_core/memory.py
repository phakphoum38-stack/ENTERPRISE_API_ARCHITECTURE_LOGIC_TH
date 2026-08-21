from __future__ import annotations

from collections import deque
from threading import RLock
from typing import Iterable

from .models import ConversationTurn


class MemoryStore:
    """Bounded, thread-safe conversation memory with explicit export/import."""

    def __init__(self, max_turns: int = 200) -> None:
        if max_turns < 1:
            raise ValueError("max_turns must be positive")
        self._turns: deque[ConversationTurn] = deque(maxlen=max_turns)
        self._lock = RLock()

    def append(self, turn: ConversationTurn) -> None:
        if turn.role not in {"system", "user", "assistant", "tool"}:
            raise ValueError("unsupported conversation role")
        if not turn.content.strip():
            raise ValueError("conversation content cannot be empty")
        with self._lock:
            self._turns.append(turn)

    def extend(self, turns: Iterable[ConversationTurn]) -> None:
        for turn in turns:
            self.append(turn)

    def recent(self, limit: int = 20) -> tuple[ConversationTurn, ...]:
        if limit < 1:
            raise ValueError("limit must be positive")
        with self._lock:
            return tuple(list(self._turns)[-limit:])

    def search(self, text: str) -> tuple[ConversationTurn, ...]:
        needle = text.strip().casefold()
        if not needle:
            return ()
        with self._lock:
            return tuple(turn for turn in self._turns if needle in turn.content.casefold())

    def export(self) -> tuple[ConversationTurn, ...]:
        with self._lock:
            return tuple(self._turns)

    def clear(self) -> None:
        with self._lock:
            self._turns.clear()
