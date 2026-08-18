from __future__ import annotations

from threading import RLock


class IdempotencyRegistry:
    """Thread-safe in-process guard for replay delivery keys.

    A durable implementation can replace this registry while preserving the
    claim/release contract used by ReplayAdapter.
    """

    def __init__(self) -> None:
        self._claimed: set[str] = set()
        self._lock = RLock()

    def claim(self, key: str) -> bool:
        if not key:
            raise ValueError("idempotency key is required")
        with self._lock:
            if key in self._claimed:
                return False
            self._claimed.add(key)
            return True

    def release(self, key: str) -> None:
        with self._lock:
            self._claimed.discard(key)
