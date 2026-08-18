from __future__ import annotations

from .sqlite_store import SQLiteDLQStore


class DLQRecoveryManager:
    """Recover replay records left in REPLAYING after a process crash."""

    def __init__(self, store: SQLiteDLQStore) -> None:
        self._store = store

    def recover(self) -> list[str]:
        """Reset interrupted replays to AVAILABLE and return task ids.

        Delivery is not attempted here. The existing replay path remains the
        single execution path; recovery only repairs durable state so a later
        replay can safely enqueue through the normal adapter.
        """
        recovered: list[str] = []
        for record in self._store.recover_replaying():
            self._store.reset_replaying(record.task_id)
            recovered.append(record.task_id)
        return recovered
