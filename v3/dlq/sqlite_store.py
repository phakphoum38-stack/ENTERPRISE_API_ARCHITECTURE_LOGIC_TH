from __future__ import annotations

import sqlite3
from threading import RLock

from .models import DLQRecord, DLQStatus


class SQLiteDLQStore:
    """Durable DLQ store with restart-safe replay state."""

    def __init__(self, database: str = ":memory:") -> None:
        self._db = sqlite3.connect(database, check_same_thread=False)
        self._lock = RLock()
        with self._db:
            self._db.execute(
                """CREATE TABLE IF NOT EXISTS dlq_records (
                    task_id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    delivery_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    attempt INTEGER NOT NULL,
                    max_attempts INTEGER NOT NULL,
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    payload_reference TEXT NOT NULL,
                    status TEXT NOT NULL,
                    replay_count INTEGER NOT NULL DEFAULT 0
                )"""
            )

    def put(self, record: DLQRecord) -> None:
        with self._lock, self._db:
            try:
                self._db.execute(
                    """INSERT INTO dlq_records
                    (task_id,event_id,delivery_id,idempotency_key,attempt,max_attempts,
                     error_type,error_message,payload_reference,status,replay_count)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (record.task_id, record.event_id, record.delivery_id,
                     record.idempotency_key, record.attempt, record.max_attempts,
                     record.error_type, record.error_message, record.payload_reference,
                     record.status.value, record.replay_count),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError(f"DLQ record already exists: {record.task_id}") from exc

    def get(self, task_id: str) -> DLQRecord | None:
        with self._lock:
            row = self._db.execute(
                "SELECT * FROM dlq_records WHERE task_id = ?", (task_id,)
            ).fetchone()
        return self._from_row(row) if row else None

    def mark_replaying(self, task_id: str) -> DLQRecord:
        with self._lock, self._db:
            record = self.get(task_id)
            if record is None:
                raise KeyError(task_id)
            if record.status is not DLQStatus.AVAILABLE:
                raise ValueError(f"record is not replayable: {record.status.value}")
            self._db.execute(
                "UPDATE dlq_records SET status = ? WHERE task_id = ?",
                (DLQStatus.REPLAYING.value, task_id),
            )
            return self.get(task_id)  # type: ignore[return-value]

    def mark_replayed(self, task_id: str) -> DLQRecord:
        with self._lock, self._db:
            record = self.get(task_id)
            if record is None:
                raise KeyError(task_id)
            self._db.execute(
                "UPDATE dlq_records SET status = ?, replay_count = replay_count + 1 WHERE task_id = ?",
                (DLQStatus.REPLAYED.value, task_id),
            )
            return self.get(task_id)  # type: ignore[return-value]

    def recover_replaying(self) -> list[DLQRecord]:
        """Return in-flight records so a restarted process can recover them."""
        with self._lock:
            rows = self._db.execute(
                "SELECT * FROM dlq_records WHERE status = ?",
                (DLQStatus.REPLAYING.value,),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def reset_replaying(self, task_id: str) -> DLQRecord:
        with self._lock, self._db:
            self._db.execute(
                "UPDATE dlq_records SET status = ? WHERE task_id = ? AND status = ?",
                (DLQStatus.AVAILABLE.value, task_id, DLQStatus.REPLAYING.value),
            )
            record = self.get(task_id)
            if record is None:
                raise KeyError(task_id)
            return record

    def close(self) -> None:
        with self._lock:
            self._db.close()

    @staticmethod
    def _from_row(row: tuple) -> DLQRecord:
        return DLQRecord(
            task_id=row[0], event_id=row[1], delivery_id=row[2],
            idempotency_key=row[3], attempt=row[4], max_attempts=row[5],
            error_type=row[6], error_message=row[7], payload_reference=row[8],
            status=DLQStatus(row[9]), replay_count=row[10],
        )
