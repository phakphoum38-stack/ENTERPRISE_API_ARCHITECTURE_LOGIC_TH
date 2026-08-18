from __future__ import annotations

from typing import Protocol

from .models import DLQRecord


class ReplayQueue(Protocol):
    """Existing queue boundary used by DLQ replay.

    The adapter deliberately depends only on ``enqueue`` so V3.4 does not
    create a second queue implementation or execution path.
    """

    def enqueue(self, record: DLQRecord) -> None: ...


class DLQReplayQueueAdapter:
    def __init__(self, queue: ReplayQueue) -> None:
        self._queue = queue

    def enqueue(self, record: DLQRecord) -> None:
        self._queue.enqueue(record)
