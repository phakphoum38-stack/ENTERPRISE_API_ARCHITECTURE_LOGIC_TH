from __future__ import annotations

from typing import Callable

from .idempotency import IdempotencyRegistry
from .models import DLQRecord
from .service import DLQService


class ReplayAdapter:
    """Safely re-enqueue a DLQ record through the existing queue boundary."""

    def __init__(self, service: DLQService, idempotency: IdempotencyRegistry) -> None:
        self.service = service
        self.idempotency = idempotency

    def replay(self, task_id: str, enqueue: Callable[[DLQRecord], None]) -> DLQRecord:
        record = self.service.store.get(task_id)
        if record is None:
            raise KeyError(task_id)
        if not self.idempotency.claim(record.idempotency_key):
            raise ValueError("duplicate replay")
        try:
            return self.service.replay(task_id, enqueue)
        except Exception:
            # The delivery did not complete, so the key must remain reusable.
            self.idempotency.release(record.idempotency_key)
            raise
