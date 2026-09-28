from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


EventConsumer = Any


@dataclass(frozen=True)
class WorkflowEvent:
    event_id: str
    event_type: str
    occurred_at: str
    workflow_id: str
    task_id: str
    correlation_id: str
    causation_id: str
    sequence: int
    producer: str
    payload: dict[str, Any]


class DurableWorkflowEventStore:
    """Append-only workflow events with durable consumer idempotency."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS workflow_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    workflow_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    correlation_id TEXT NOT NULL,
                    causation_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    producer TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    UNIQUE(workflow_id, task_id, sequence)
                )"""
            )
            db.execute(
                """CREATE TABLE IF NOT EXISTS event_deliveries (
                    event_id TEXT NOT NULL,
                    consumer_key TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'claimed',
                    attempts INTEGER NOT NULL DEFAULT 1,
                    delivered_at TEXT NOT NULL,
                    last_error TEXT,
                    lease_until TEXT,
                    delivery_token TEXT,
                    PRIMARY KEY(event_id, consumer_key),
                    FOREIGN KEY(event_id) REFERENCES workflow_events(event_id)
                )"""
            )
            columns = {row[1] for row in db.execute("PRAGMA table_info(event_deliveries)")}
            if "lease_until" not in columns:
                db.execute("ALTER TABLE event_deliveries ADD COLUMN lease_until TEXT")
            if "delivery_token" not in columns:
                db.execute("ALTER TABLE event_deliveries ADD COLUMN delivery_token TEXT")

    def append(
        self,
        event_type: str,
        *,
        workflow_id: str,
        task_id: str,
        correlation_id: str,
        causation_id: str,
        producer: str,
        payload: dict[str, Any] | None = None,
        event_id: str | None = None,
    ) -> WorkflowEvent:
        values = (workflow_id, task_id, correlation_id, causation_id, producer)
        if not all(str(value).strip() for value in values) or not event_type.strip():
            raise ValueError("event type and event identifiers are required")
        event_id = event_id or uuid.uuid4().hex
        occurred_at = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.path) as db:
            existing = db.execute(
                "SELECT * FROM workflow_events WHERE event_id=?", (event_id,)
            ).fetchone()
            if existing is not None:
                return self._from_row(existing)
            sequence = db.execute(
                "SELECT COALESCE(MAX(sequence), 0) + 1 FROM workflow_events WHERE workflow_id=? AND task_id=?",
                (workflow_id, task_id),
            ).fetchone()[0]
            db.execute(
                "INSERT INTO workflow_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    event_id,
                    event_type,
                    occurred_at,
                    workflow_id,
                    task_id,
                    correlation_id,
                    causation_id,
                    sequence,
                    producer,
                    json.dumps(payload or {}, sort_keys=True),
                ),
            )
            row = db.execute(
                "SELECT * FROM workflow_events WHERE event_id=?", (event_id,)
            ).fetchone()
        return self._from_row(row)

    def list_events(self, workflow_id: str, task_id: str | None = None) -> list[WorkflowEvent]:
        query = "SELECT * FROM workflow_events WHERE workflow_id=?"
        params: tuple[str, ...] = (workflow_id,)
        if task_id is not None:
            query += " AND task_id=?"
            params += (task_id,)
        query += " ORDER BY task_id, sequence"
        with sqlite3.connect(self.path) as db:
            rows = db.execute(query, params).fetchall()
        return [self._from_row(row) for row in rows]

    def get_event(self, event_id: str) -> WorkflowEvent:
        with sqlite3.connect(self.path) as db:
            row = db.execute(
                "SELECT * FROM workflow_events WHERE event_id=?", (event_id,)
            ).fetchone()
        if row is None:
            raise ValueError("event does not exist")
        return self._from_row(row)

    def claim_delivery(self, event_id: str, consumer_key: str, *, lease_seconds: int = 30) -> bool:
        return self.claim_delivery_token(
            event_id, consumer_key, lease_seconds=lease_seconds
        ) is not None

    def claim_delivery_token(
        self, event_id: str, consumer_key: str, *, lease_seconds: int = 30
    ) -> str | None:
        """Claim an event and return a token required for ownership-sensitive completion."""
        if not event_id.strip() or not consumer_key.strip():
            raise ValueError("event_id and consumer_key are required")
        if lease_seconds < 1:
            raise ValueError("lease_seconds must be at least 1")
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        lease_until = (now + timedelta(seconds=lease_seconds)).isoformat()
        delivery_token = uuid.uuid4().hex
        with sqlite3.connect(self.path) as db:
            exists = db.execute(
                "SELECT 1 FROM workflow_events WHERE event_id=?", (event_id,)
            ).fetchone()
            if exists is None:
                raise ValueError("event does not exist")
            cursor = db.execute(
                """INSERT INTO event_deliveries
                                     (event_id, consumer_key, status, attempts, delivered_at, lease_until, delivery_token)
                                     VALUES (?, ?, 'claimed', 1, ?, ?, ?)
                   ON CONFLICT(event_id, consumer_key) DO UPDATE SET
                     status='claimed', attempts=event_deliveries.attempts + 1,
                                         delivered_at=excluded.delivered_at, last_error=NULL,
                                         lease_until=excluded.lease_until,
                                         delivery_token=excluded.delivery_token
                                     WHERE event_deliveries.status='failed'
                                            OR (event_deliveries.status='claimed' AND event_deliveries.lease_until<=?)""",
                                (event_id, consumer_key, now_iso, lease_until, delivery_token, now_iso),
            )
            return delivery_token if cursor.rowcount == 1 else None

    def complete_delivery(
        self, event_id: str, consumer_key: str, delivery_token: str | None = None
    ) -> None:
        with sqlite3.connect(self.path) as db:
            token_clause = " AND delivery_token=?" if delivery_token is not None else ""
            params = (event_id, consumer_key, delivery_token) if delivery_token is not None else (event_id, consumer_key)
            cursor = db.execute(
                "UPDATE event_deliveries SET status='completed', lease_until=NULL, delivery_token=NULL WHERE event_id=? AND consumer_key=? AND status='claimed'" + token_clause,
                params,
            )
            if cursor.rowcount != 1:
                raise ValueError("delivery is not actively claimed")

    def fail_delivery(
        self,
        event_id: str,
        consumer_key: str,
        error: str,
        delivery_token: str | None = None,
    ) -> None:
        if not error.strip():
            raise ValueError("delivery error is required")
        with sqlite3.connect(self.path) as db:
            token_clause = " AND delivery_token=?" if delivery_token is not None else ""
            params = (error, event_id, consumer_key, delivery_token) if delivery_token is not None else (error, event_id, consumer_key)
            cursor = db.execute(
                "UPDATE event_deliveries SET status='failed', last_error=?, lease_until=NULL, delivery_token=NULL WHERE event_id=? AND consumer_key=? AND status='claimed'" + token_clause,
                params,
            )
            if cursor.rowcount != 1:
                raise ValueError("delivery is not actively claimed")

    def metrics(self, workflow_id: str | None = None) -> dict[str, int]:
        """Return safe delivery counters without exposing event payloads."""
        scope = ""
        params: tuple[str, ...] = ()
        if workflow_id is not None:
            scope = " WHERE workflow_id=?"
            params = (workflow_id,)
        with sqlite3.connect(self.path) as db:
            event_count = db.execute(
                f"SELECT COUNT(*) FROM workflow_events{scope}", params
            ).fetchone()[0]
            delivery_query = (
                "SELECT d.status, COUNT(*) FROM event_deliveries d "
                "JOIN workflow_events e ON e.event_id=d.event_id"
            )
            if workflow_id is not None:
                delivery_query += " WHERE e.workflow_id=?"
            delivery_query += " GROUP BY d.status"
            delivery_rows = db.execute(delivery_query, params).fetchall()
            attempts = db.execute(
                "SELECT COALESCE(SUM(d.attempts), 0) FROM event_deliveries d "
                "JOIN workflow_events e ON e.event_id=d.event_id"
                + (" WHERE e.workflow_id=?" if workflow_id is not None else ""),
                params,
            ).fetchone()[0]
        result = {"event_count": event_count, "delivery_attempts": attempts}
        result.update({f"delivery_{status}": count for status, count in delivery_rows})
        return result

    def deliver(self, event_id: str, consumer_key: str, consumer: EventConsumer) -> bool:
        """Deliver one event once; failed deliveries remain retryable."""
        if not callable(consumer):
            raise TypeError("consumer must be callable")
        delivery_token = self.claim_delivery_token(event_id, consumer_key)
        if delivery_token is None:
            return False
        event = self.get_event(event_id)
        try:
            consumer(event)
        except Exception as exc:
            self.fail_delivery(
                event_id, consumer_key, f"{type(exc).__name__}: {exc}", delivery_token
            )
            raise
        self.complete_delivery(event_id, consumer_key, delivery_token)
        return True

    def event_sink(
        self,
        *,
        workflow_id: str,
        correlation_id: str,
        producer: str = "runtime",
    ):
        """Adapt runner/worker event callbacks to durable workflow events."""
        if not workflow_id.strip() or not correlation_id.strip():
            raise ValueError("workflow_id and correlation_id are required")

        def sink(event_type: str, task_id: str, detail: dict[str, Any]) -> None:
            causation_id = str(detail.get("causation_id") or "root")
            self.append(
                event_type,
                workflow_id=workflow_id,
                task_id=task_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
                producer=producer,
                payload=dict(detail),
            )

        return sink

    @staticmethod
    def _from_row(row: tuple[Any, ...]) -> WorkflowEvent:
        return WorkflowEvent(
            event_id=row[0], event_type=row[1], occurred_at=row[2],
            workflow_id=row[3], task_id=row[4], correlation_id=row[5],
            causation_id=row[6], sequence=row[7], producer=row[8],
            payload=json.loads(row[9]),
        )
