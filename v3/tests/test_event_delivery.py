from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from v3.research_os_v3.event_delivery import DurableEventDelivery, EventDeliveryOwnershipError, EventEnvelope


def event() -> EventEnvelope:
    return EventEnvelope(
        event_id="evt-1", event_type="task.completed",
        occurred_at=datetime.now(timezone.utc).isoformat(),
        workflow_id="wf-1", task_id="task-1",
        correlation_id="corr-1", causation_id="cause-1",
        sequence=1, producer="worker", payload={"ok": True},
    )


def test_delivery_is_durable_and_duplicate_registration_is_suppressed(tmp_path: Path) -> None:
    path = tmp_path / "events.db"
    ledger = DurableEventDelivery(path)
    ledger.append(event())

    first = ledger.register_delivery(
        event_id="evt-1", consumer="consumer-a", delivery_id="delivery-1", idempotency_key="idem-1"
    )
    duplicate = ledger.register_delivery(
        event_id="evt-1", consumer="consumer-a", delivery_id="delivery-2", idempotency_key="idem-1"
    )
    assert first.delivery_id == duplicate.delivery_id == "delivery-1"

    claimed = ledger.claim("delivery-1")
    assert claimed is not None and claimed.lease_id is not None
    ledger.ack("delivery-1", claimed.lease_id)

    restarted = DurableEventDelivery(path)
    persisted = restarted.get_delivery("delivery-1")
    assert persisted is not None
    assert persisted.status == "acked"


def test_claim_is_single_owner_and_ack_is_idempotent(tmp_path: Path) -> None:
    ledger = DurableEventDelivery(tmp_path / "events.db")
    ledger.append(event())
    ledger.register_delivery(event_id="evt-1", consumer="consumer-a", delivery_id="delivery-1", idempotency_key="idem-1")

    first = ledger.claim("delivery-1")
    second = ledger.claim("delivery-1")
    assert first is not None and first.lease_id is not None
    assert second is None

    ledger.ack("delivery-1", first.lease_id)
    ledger.ack("delivery-1", first.lease_id)
    assert ledger.get_delivery("delivery-1").status == "acked"


def test_stale_delivery_lease_cannot_ack_after_recovery(tmp_path: Path) -> None:
    ledger = DurableEventDelivery(tmp_path / "events.db", lease_seconds=30)
    ledger.append(event())
    ledger.register_delivery(event_id="evt-1", consumer="consumer-a", delivery_id="delivery-1", idempotency_key="idem-1")
    first = ledger.claim("delivery-1")
    assert first is not None and first.lease_id is not None

    with sqlite3.connect(ledger.path) as db:
        db.execute(
            "UPDATE deliveries SET lease_until=? WHERE delivery_id=?",
            ("2000-01-01T00:00:00+00:00", "delivery-1"),
        )
        db.commit()

    assert ledger.recover_expired() == 1
    second = ledger.claim("delivery-1")
    assert second is not None and second.lease_id is not None
    with pytest.raises(EventDeliveryOwnershipError):
        ledger.ack("delivery-1", first.lease_id)
    ledger.ack("delivery-1", second.lease_id)


def test_unknown_event_fails_closed(tmp_path: Path) -> None:
    ledger = DurableEventDelivery(tmp_path / "events.db")
    with pytest.raises(KeyError):
        ledger.register_delivery(event_id="missing", consumer="consumer-a", delivery_id="delivery-1", idempotency_key="idem-1")
