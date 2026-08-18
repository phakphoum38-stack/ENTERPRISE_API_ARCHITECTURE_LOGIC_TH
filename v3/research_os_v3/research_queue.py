from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class QueueState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    RETRY = "retry"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True)
class QueueItem:
    item_id: int
    task_id: str
    payload: dict[str, object]
    attempts: int
    max_attempts: int
    state: QueueState


class DurableResearchQueue:
    """Small durable queue adapter; production brokers can implement the same contract."""

    def __init__(self, path: Path | str = ":memory:") -> None:
        self.path = str(path)
        self._db = sqlite3.connect(self.path, isolation_level=None)
        self._db.row_factory = sqlite3.Row
        self._db.execute(
            """CREATE TABLE IF NOT EXISTS research_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL,
                state TEXT NOT NULL,
                error TEXT
            )"""
        )

    def enqueue(self, *, task_id: str, payload: dict[str, object], max_attempts: int = 3) -> int:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        cur = self._db.execute(
            "INSERT INTO research_queue(task_id,payload,max_attempts,state) VALUES(?,?,?,?,?)",
            (task_id, json.dumps(payload, sort_keys=True), max_attempts, QueueState.QUEUED),
        )
        return int(cur.lastrowid)

    def claim_ready(self) -> QueueItem | None:
        self._db.execute("BEGIN IMMEDIATE")
        try:
            row = self._db.execute(
                "SELECT * FROM research_queue WHERE state IN (?,?) ORDER BY id LIMIT 1",
                (QueueState.QUEUED, QueueState.RETRY),
            ).fetchone()
            if row is None:
                self._db.execute("COMMIT")
                return None
            self._db.execute("UPDATE research_queue SET state=?, attempts=attempts+1 WHERE id=?", (QueueState.RUNNING, row["id"]))
            self._db.execute("COMMIT")
            return QueueItem(row["id"], row["task_id"], json.loads(row["payload"]), row["attempts"] + 1, row["max_attempts"], QueueState.RUNNING)
        except Exception:
            self._db.execute("ROLLBACK")
            raise

    def ack(self, item_id: int) -> None:
        self._db.execute("UPDATE research_queue SET state=? WHERE id=?", (QueueState.SUCCEEDED, item_id))

    def fail(self, item_id: int, *, error: str) -> QueueState:
        row = self._db.execute("SELECT attempts,max_attempts FROM research_queue WHERE id=?", (item_id,)).fetchone()
        if row is None:
            raise KeyError(item_id)
        state = QueueState.RETRY if row["attempts"] < row["max_attempts"] else QueueState.FAILED
        self._db.execute("UPDATE research_queue SET state=?, error=? WHERE id=?", (state, error, item_id))
        return state

    def close(self) -> None:
        self._db.close()
