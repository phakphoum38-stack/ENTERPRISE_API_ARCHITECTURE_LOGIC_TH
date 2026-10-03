import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from v3.research_os_v3.event_delivery import (
    DurableEventDelivery,
    EventDeliveryOwnershipError,
    EventEnvelope,
)


def make_event():
    return EventEnvelope(
        event_id="evt-1",
        event_type="task.completed",
        occurred_at=datetime.now(timezone.utc).isoformat(),
        workflow_id="wf-1",
        task_id="task-1",
        correlation_id="corr-1",
        causation_id="cause-1",
        sequence=1,
        producer="worker",
        payload={"ok": True},
    )


class EventDeliveryTests(unittest.TestCase):
    def _database_path(self, temp_dir):
        return Path(temp_dir) / f"{self.id().replace('.', '_')}.db"

    def test_delivery_is_durable_and_duplicate_registration_is_suppressed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self._database_path(temp_dir)
            ledger = DurableEventDelivery(path)

            ledger.append(make_event())

            first = ledger.register_delivery(
                event_id="evt-1",
                consumer="consumer-a",
                delivery_id="delivery-1",
                idempotency_key="idem-1",
            )
            duplicate = ledger.register_delivery(
                event_id="evt-1",
                consumer="consumer-a",
                delivery_id="delivery-2",
                idempotency_key="idem-1",
            )

            self.assertEqual("delivery-1", first.delivery_id)
            self.assertEqual("delivery-1", duplicate.delivery_id)

            claimed = ledger.claim("delivery-1")
            self.assertIsNotNone(claimed)
            self.assertIsNotNone(claimed.lease_id)

            ledger.ack("delivery-1", claimed.lease_id)

            restarted = DurableEventDelivery(path)
            self.assertEqual(
                "acked",
                restarted.get_delivery("delivery-1").status,
            )

    def test_claim_is_single_owner_and_ack_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self._database_path(temp_dir)
            ledger = DurableEventDelivery(path)

            ledger.append(make_event())
            ledger.register_delivery(
                event_id="evt-1",
                consumer="consumer-a",
                delivery_id="delivery-1",
                idempotency_key="idem-1",
            )

            first = ledger.claim("delivery-1")
            second = ledger.claim("delivery-1")

            self.assertIsNotNone(first)
            self.assertIsNotNone(first.lease_id)
            self.assertIsNone(second)

            ledger.ack("delivery-1", first.lease_id)
            ledger.ack("delivery-1", first.lease_id)

            self.assertEqual(
                "acked",
                ledger.get_delivery("delivery-1").status,
            )

    def test_stale_delivery_lease_cannot_ack_after_recovery(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self._database_path(temp_dir)
            ledger = DurableEventDelivery(path)

            ledger.append(make_event())
            ledger.register_delivery(
                event_id="evt-1",
                consumer="consumer-a",
                delivery_id="delivery-1",
                idempotency_key="idem-1",
            )

            first = ledger.claim("delivery-1")
            self.assertIsNotNone(first)
            self.assertIsNotNone(first.lease_id)

            db = sqlite3.connect(ledger.path)
            try:
                db.execute(
                    "UPDATE deliveries "
                    "SET lease_until=? "
                    "WHERE delivery_id=?",
                    (
                        "2000-01-01T00:00:00+00:00",
                        "delivery-1",
                    ),
                )
                db.commit()
            finally:
                db.close()

            self.assertEqual(1, ledger.recover_expired())

            second = ledger.claim("delivery-1")
            self.assertIsNotNone(second)
            self.assertIsNotNone(second.lease_id)
            self.assertNotEqual(
                first.lease_id,
                second.lease_id,
            )

            with self.assertRaises(EventDeliveryOwnershipError):
                ledger.ack("delivery-1", first.lease_id)

            ledger.ack("delivery-1", second.lease_id)

    def test_unknown_event_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self._database_path(temp_dir)
            ledger = DurableEventDelivery(path)

            with self.assertRaises(KeyError):
                ledger.register_delivery(
                    event_id="missing",
                    consumer="consumer-a",
                    delivery_id="delivery-1",
                    idempotency_key="idem-1",
                )


if __name__ == "__main__":
    unittest.main()
