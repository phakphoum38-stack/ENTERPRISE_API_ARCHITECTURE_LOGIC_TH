from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


class EventDeliveryOwnershipError(RuntimeError):
    """Raised when a delivery is not owned by the supplied lease."""


@dataclass(frozen=True)
class EventEnvelope:
    event_id: str
    event_type: str
    occurred_at: str
    workflow_id: str
    task_id: str
    correlation_id: str
    causation_id: str
    sequence: int
    producer: str
    payload: dict[str, object]


@dataclass(frozen=True)
class Delivery:
    delivery_id: str
    event_id: str
    consumer: str
    idempotency_key: str
    status: str
    lease_id: str | None = None
    lease_until: str | None = None


class DurableEventDelivery:
    """Append-only event log plus durable consumer delivery ledger.

    This is a persistence boundary, not a second event bus or execution path.
    Delivery is at-least-once and consumer acknowledgement is idempotent.
    """

    def __init__(self, path: Path, *, lease_seconds: int = 30) -> None:
        if lease_seconds < 1:
            raise ValueError("lease_seconds must be at least 1")
        self.path = path
        self.lease_seconds = lease_seconds
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, occurred_at TEXT NOT NULL,
                workflow_id TEXT NOT NULL, task_id TEXT NOT NULL, correlation_id TEXT NOT NULL,
                causation_id TEXT NOT NULL, sequence INTEGER NOT NULL, producer TEXT NOT NULL,
                payload TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS deliveries (
                delivery_id TEXT PRIMARY KEY, event_id TEXT NOT NULL, consumer TEXT NOT NULL,
                idempotency_key TEXT NOT NULL UNIQUE, status TEXT NOT NULL,
                lease_id TEXT, lease_until TEXT)""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_delivery_ready ON deliveries(consumer,status,lease_until)")

    def append(self, event: EventEnvelope) -> None:
        payload = json.dumps(event.payload, sort_keys=True, separators=(",", ":"))
        with sqlite3.connect(self.path) as db:
            try:
                db.execute("""INSERT INTO events
                    (event_id,event_type,occurred_at,workflow_id,task_id,correlation_id,
                     causation_id,sequence,producer,payload) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (event.event_id,event.event_type,event.occurred_at,event.workflow_id,event.task_id,
                     event.correlation_id,event.causation_id,event.sequence,event.producer,payload))
            except sqlite3.IntegrityError as exc:
                raise ValueError(f"event already exists: {event.event_id}") from exc

    def register_delivery(self, *, event_id: str, consumer: str, delivery_id: str, idempotency_key: str) -> Delivery:
        if not all((event_id, consumer, delivery_id, idempotency_key)):
            raise ValueError("event_id, consumer, delivery_id and idempotency_key are required")
        with sqlite3.connect(self.path) as db:
            if db.execute("SELECT 1 FROM events WHERE event_id=?", (event_id,)).fetchone() is None:
                raise KeyError(event_id)
            try:
                db.execute("INSERT INTO deliveries (delivery_id,event_id,consumer,idempotency_key,status) VALUES (?,?,?,?,?)",
                           (delivery_id,event_id,consumer,idempotency_key,"available"))
            except sqlite3.IntegrityError:
                row = db.execute("SELECT delivery_id,event_id,consumer,idempotency_key,status,lease_id,lease_until FROM deliveries WHERE idempotency_key=?",
                                 (idempotency_key,)).fetchone()
                if row is None:
                    raise
                return Delivery(*row)
        return Delivery(delivery_id,event_id,consumer,idempotency_key,"available")

    def claim(self, delivery_id: str) -> Delivery | None:
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        until = (now + timedelta(seconds=self.lease_seconds)).isoformat()
        lease_id = uuid.uuid4().hex
        with sqlite3.connect(self.path, timeout=30, isolation_level=None) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT delivery_id,event_id,consumer,idempotency_key,status,lease_id,lease_until FROM deliveries WHERE delivery_id=? AND (status='available' OR (status='delivering' AND lease_until<=?))", (delivery_id,now_iso)).fetchone()
            if row is None:
                return None
            db.execute("UPDATE deliveries SET status='delivering',lease_id=?,lease_until=? WHERE delivery_id=? AND (status='available' OR (status='delivering' AND lease_until<=?))", (lease_id,until,delivery_id,now_iso))
        return Delivery(row[0],row[1],row[2],row[3],"delivering",lease_id,until)

    def ack(self, delivery_id: str, lease_id: str) -> None:
        if not lease_id:
            raise ValueError("lease_id is required")
        with sqlite3.connect(self.path) as db:
            cursor = db.execute("UPDATE deliveries SET status='acked',lease_id=NULL,lease_until=NULL WHERE delivery_id=? AND status='delivering' AND lease_id=?", (delivery_id,lease_id))
            if cursor.rowcount == 1:
                return
            row = db.execute("SELECT status FROM deliveries WHERE delivery_id=?", (delivery_id,)).fetchone()
            if row is None:
                raise KeyError(delivery_id)
            if row[0] == "acked":
                return
            raise EventDeliveryOwnershipError("delivery is not owned by the supplied lease")

    def recover_expired(self) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.path) as db:
            cursor = db.execute("UPDATE deliveries SET status='available',lease_id=NULL,lease_until=NULL WHERE status='delivering' AND lease_until<=?", (now,))
            return cursor.rowcount

    def get_delivery(self, delivery_id: str) -> Delivery | None:
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT delivery_id,event_id,consumer,idempotency_key,status,lease_id,lease_until FROM deliveries WHERE delivery_id=?", (delivery_id,)).fetchone()
        return Delivery(*row) if row else None

    def close(self) -> None:
        return None
