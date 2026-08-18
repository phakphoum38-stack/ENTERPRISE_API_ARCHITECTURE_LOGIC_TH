from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class QueueTask:
    task_id: str
    research_id: str
    payload: Mapping[str, object]
    attempts: int = 0


class DurableTaskQueue:
    """Small durable queue boundary.

    SQLite is the portable reference adapter. Production deployments can
    replace this implementation with RabbitMQ/Kafka without changing Runner.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS research_queue (
                    task_id TEXT PRIMARY KEY,
                    research_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'queued',
                    available_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )"""
            )
            db.execute(
                "CREATE INDEX IF NOT EXISTS idx_research_queue_ready "
                "ON research_queue(status, available_at)"
            )

    def enqueue(self, task: QueueTask) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.path) as db:
            db.execute(
                "INSERT INTO research_queue "
                "(task_id,research_id,payload,attempts,status,available_at,updated_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (task.task_id, task.research_id, json.dumps(dict(task.payload), sort_keys=True),
                 task.attempts, "queued", now, now),
            )

    def claim(self) -> QueueTask | None:
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT task_id,research_id,payload,attempts FROM research_queue "
                "WHERE status='queued' AND available_at<=? ORDER BY available_at LIMIT 1",
                (now,),
            ).fetchone()
            if row is None:
                return None
            db.execute(
                "UPDATE research_queue SET status='running', updated_at=? WHERE task_id=?",
                (now, row[0]),
            )
        return QueueTask(row[0], row[1], json.loads(row[2]), row[3])

    def ack(self, task_id: str) -> None:
        self._set_status(task_id, "completed")

    def retry(self, task_id: str, *, delay_seconds: int = 0) -> None:
        now = datetime.now(timezone.utc)
        available = (now.timestamp() + max(0, delay_seconds))
        available_at = datetime.fromtimestamp(available, tz=timezone.utc).isoformat()
        with sqlite3.connect(self.path) as db:
            db.execute(
                "UPDATE research_queue SET status='queued', attempts=attempts+1, "
                "available_at=?, updated_at=? WHERE task_id=?",
                (available_at, now.isoformat(), task_id),
            )

    def fail(self, task_id: str) -> None:
        self._set_status(task_id, "failed")

    def _set_status(self, task_id: str, status: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.path) as db:
            db.execute(
                "UPDATE research_queue SET status=?, updated_at=? WHERE task_id=?",
                (status, now, task_id),
            )
