from __future__ import annotations

from dataclasses import replace
from typing import Callable

from .models import DLQRecord, DLQStatus
from .store import InMemoryDLQStore


class DLQService:
    def __init__(self, store: InMemoryDLQStore) -> None:
        self.store = store

    def dead_letter(self, record: DLQRecord) -> None:
        if record.status is not DLQStatus.AVAILABLE:
            raise ValueError("new DLQ records must start as available")
        self.store.put(record)

    def replay(
        self,
        task_id: str,
        enqueue: Callable[[DLQRecord], None],
    ) -> DLQRecord:
        record = self.store.mark_replaying(task_id)
        try:
            enqueue(record)
        except Exception:
            # Keep the record replaying; a durable implementation should use
            # an explicit recovery/timeout transition rather than silently
            # claiming the replay succeeded.
            raise
        return self.store.mark_replayed(task_id)
