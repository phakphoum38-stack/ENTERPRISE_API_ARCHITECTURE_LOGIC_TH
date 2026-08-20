from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class QueueTask:
    task_id: str
    research_id: str
    payload: Mapping[str, object]
    attempts: int = 0
    lease_id: str | None = None
    lease_until: str | None = None


class LeaseOwnershipError(RuntimeError):
    """Raised when a worker tries to mutate a task without its active lease."""


class DurableTaskQueue:
    """Durable queue boundary with expiring worker leases."""

    def __init__(self, path: Path, *, default_lease_seconds: int = 30) -> None:
        if default_lease_seconds < 1:
            raise ValueError("default_lease_seconds must be at least 1")
        self.path = path
        self.default_lease_seconds = default_lease_seconds
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
                    updated_at TEXT NOT NULL,
                    lease_id TEXT,
                    lease_until TEXT,
                    worker_id TEXT
                )"""
            )
            columns = {row[1] for row in db.execute("PRAGMA table_info(research_queue)")}
            for name, definition in (
                ("lease_id", "TEXT"),
                ("lease_until", "TEXT"),
                ("worker_id", "TEXT"),
            ):
                if name not in columns:
                    db.execute(f"ALTER TABLE research_queue ADD COLUMN {name} {definition}")
            db.execute("CREATE INDEX IF NOT EXISTS idx_research_queue_ready ON research_queue(status, available_at)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_research_queue_lease ON research_queue(status, lease_until)")

    def enqueue(self, task: QueueTask) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.path) as db:
            db.execute(
                "INSERT INTO research_queue "
                "(task_id,research_id,payload,attempts,status,available_at,updated_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (task.task_id, task.research_id, json.dumps(dict(task.payload), sort_keys=True), task.attempts, "queued", now, now),
            )

    def claim(self, *, worker_id: str | None = None, lease_seconds: int | None = None) -> QueueTask | None:
        lease_seconds = self.default_lease_seconds if lease_seconds is None else lease_seconds
        if lease_seconds < 1:
            raise ValueError("lease_seconds must be at least 1")
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        lease_until = (now + timedelta(seconds=lease_seconds)).isoformat()
        lease_id = uuid.uuid4().hex
        with sqlite3.connect(self.path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT task_id,research_id,payload,attempts FROM research_queue "
                "WHERE status='queued' AND available_at<=? ORDER BY available_at LIMIT 1",
                (now_iso,),
            ).fetchone()
            if row is None:
                return None
            db.execute(
                "UPDATE research_queue SET status='running', updated_at=?, lease_id=?, lease_until=?, worker_id=? WHERE task_id=?",
                (now_iso, lease_id, lease_until, worker_id, row[0]),
            )
        return QueueTask(row[0], row[1], json.loads(row[2]), row[3], lease_id, lease_until)

    def renew_lease(self, task_id: str, lease_id: str, *, lease_seconds: int | None = None) -> QueueTask:
        lease_seconds = self.default_lease_seconds if lease_seconds is None else lease_seconds
        if lease_seconds < 1:
            raise ValueError("lease_seconds must be at least 1")
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        new_until = (now + timedelta(seconds=lease_seconds)).isoformat()
        with sqlite3.connect(self.path) as db:
            row = db.execute(
                "SELECT task_id,research_id,payload,attempts,lease_until FROM research_queue "
                "WHERE task_id=? AND status='running' AND lease_id=?",
                (task_id, lease_id),
            ).fetchone()
            if row is None or row[4] is None or row[4] <= now_iso:
                raise LeaseOwnershipError("task is not owned by the supplied active lease")
            db.execute(
                "UPDATE research_queue SET lease_until=?, updated_at=? WHERE task_id=? AND lease_id=?",
                (new_until, now_iso, task_id, lease_id),
            )
        return QueueTask(row[0], row[1], json.loads(row[2]), row[3], lease_id, new_until)

    def ack(self, task_id: str, lease_id: str) -> None:
        self._set_status(task_id, "completed", lease_id)

    def retry(self, task_id: str, lease_id: str, *, delay_seconds: int = 0) -> None:
        now = datetime.now(timezone.utc)
        self._assert_lease(task_id, lease_id, now)
        available_at = (now + timedelta(seconds=max(0, delay_seconds))).isoformat()
        with sqlite3.connect(self.path) as db:
            db.execute(
                "UPDATE research_queue SET status='queued', attempts=attempts+1, available_at=?, updated_at=?, lease_id=NULL, lease_until=NULL, worker_id=NULL WHERE task_id=? AND lease_id=?",
                (available_at, now.isoformat(), task_id, lease_id),
            )

    def fail(self, task_id: str, lease_id: str) -> None:
        self._set_status(task_id, "failed", lease_id)

    def recover_expired_leases(self) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.path) as db:
            cursor = db.execute(
                "UPDATE research_queue SET status='queued', available_at=?, updated_at=?, lease_id=NULL, lease_until=NULL, worker_id=NULL WHERE status='running' AND lease_until IS NOT NULL AND lease_until<=?",
                (now, now, now),
            )
            return cursor.rowcount

    def _assert_lease(self, task_id: str, lease_id: str, now: datetime) -> None:
        with sqlite3.connect(self.path) as db:
            row = db.execute(
                "SELECT lease_until FROM research_queue WHERE task_id=? AND status='running' AND lease_id=?",
                (task_id, lease_id),
            ).fetchone()
        if row is None or row[0] is None or row[0] <= now.isoformat():
            raise LeaseOwnershipError("task is not owned by the supplied active lease")

    def _set_status(self, task_id: str, status: str, lease_id: str) -> None:
        now = datetime.now(timezone.utc)
        self._assert_lease(task_id, lease_id, now)
        with sqlite3.connect(self.path) as db:
            cursor = db.execute(
                "UPDATE research_queue SET status=?, updated_at=?, lease_id=NULL, lease_until=NULL, worker_id=NULL WHERE task_id=? AND lease_id=?",
                (status, now.isoformat(), task_id, lease_id),
            )
            if cursor.rowcount != 1:
                raise LeaseOwnershipError("task ownership changed before status update")

    def close(self) -> None:
        return None
