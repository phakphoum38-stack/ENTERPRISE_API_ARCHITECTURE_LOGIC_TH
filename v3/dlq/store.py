from __future__ import annotations

from threading import RLock

from .models import DLQRecord, DLQStatus


class InMemoryDLQStore:
    """Deterministic store used by the V3.4 contract/tests.

    Production persistence can implement the same operations without changing
    the DLQ service contract.
    """

    def __init__(self) -> None:
        self._records: dict[str, DLQRecord] = {}
        self._lock = RLock()

    def put(self, record: DLQRecord) -> None:
        with self._lock:
            if record.task_id in self._records:
                raise ValueError(f"DLQ record already exists: {record.task_id}")
            self._records[record.task_id] = record

    def get(self, task_id: str) -> DLQRecord | None:
        with self._lock:
            return self._records.get(task_id)

    def mark_replaying(self, task_id: str) -> DLQRecord:
        with self._lock:
            record = self._records.get(task_id)
            if record is None:
                raise KeyError(task_id)
            if record.status is not DLQStatus.AVAILABLE:
                raise ValueError(f"record is not replayable: {record.status.value}")
            updated = DLQRecord(**{**record.__dict__, "status": DLQStatus.REPLAYING})
            self._records[task_id] = updated
            return updated

    def mark_replayed(self, task_id: str) -> DLQRecord:
        with self._lock:
            record = self._records[task_id]
            updated = DLQRecord(**{**record.__dict__, "status": DLQStatus.REPLAYED, "replay_count": record.replay_count + 1})
            self._records[task_id] = updated
            return updated
