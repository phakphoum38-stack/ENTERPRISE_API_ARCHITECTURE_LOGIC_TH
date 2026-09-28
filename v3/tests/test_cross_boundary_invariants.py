from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from v3.research_os_v3.event_delivery import DurableEventDelivery, EventEnvelope
from v3.research_os_v3.queue import DurableTaskQueue, QueueTask


class CrossBoundaryInvariantTests(unittest.TestCase):
    def _event(self) -> EventEnvelope:
        return EventEnvelope(
            event_id="evt-cross-1",
            event_type="task.completed",
            occurred_at="2026-09-18T00:00:00+00:00",
            workflow_id="wf-cross-1",
            task_id="task-cross-1",
            correlation_id="corr-cross-1",
            causation_id="cause-cross-1",
            sequence=1,
            producer="worker-a",
            payload={"status": "completed"},
        )

    def test_task_identity_survives_queue_to_event_delivery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue = DurableTaskQueue(root / "queue.db")
            delivery = DurableEventDelivery(root / "events.db")

            task = QueueTask("task-cross-1", "research-cross-1", {"input": "x"})
            queue.enqueue(task)
            claimed = queue.claim(worker_id="worker-a")
            self.assertIsNotNone(claimed)

            delivery.append(self._event())
            registered = delivery.register_delivery(
                event_id="evt-cross-1",
                consumer="consumer-a",
                delivery_id="delivery-cross-1",
                idempotency_key="task-cross-1:evt-cross-1:consumer-a",
            )
            self.assertEqual(task.task_id, registered.event_id.replace("evt-", "task-"))

            queue.ack(task.task_id, claimed.lease_id)
            active = delivery.claim(registered.delivery_id)
            self.assertIsNotNone(active)
            delivery.ack(active.delivery_id, active.lease_id)
            self.assertEqual("acked", delivery.get_delivery(active.delivery_id).status)

    def test_duplicate_event_delivery_does_not_create_second_execution_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            delivery = DurableEventDelivery(root / "events.db")
            delivery.append(self._event())

            first = delivery.register_delivery(
                event_id="evt-cross-1",
                consumer="consumer-a",
                delivery_id="delivery-1",
                idempotency_key="task-cross-1:evt-cross-1:consumer-a",
            )
            second = delivery.register_delivery(
                event_id="evt-cross-1",
                consumer="consumer-a",
                delivery_id="delivery-2",
                idempotency_key="task-cross-1:evt-cross-1:consumer-a",
            )

            self.assertEqual(first.delivery_id, second.delivery_id)
            self.assertEqual("delivery-1", second.delivery_id)

    def test_old_delivery_owner_cannot_mutate_after_new_owner_claims(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            delivery = DurableEventDelivery(root / "events.db")
            delivery.append(self._event())
            delivery.register_delivery(
                event_id="evt-cross-1",
                consumer="consumer-a",
                delivery_id="delivery-cross-1",
                idempotency_key="idem-cross-1",
            )
            old = delivery.claim("delivery-cross-1")
            self.assertIsNotNone(old)

            import sqlite3
            with sqlite3.connect(delivery.path) as db:
                db.execute(
                    "UPDATE deliveries SET lease_until=? WHERE delivery_id=?",
                    ("2000-01-01T00:00:00+00:00", "delivery-cross-1"),
                )

            self.assertEqual(1, delivery.recover_expired())
            new = delivery.claim("delivery-cross-1")
            self.assertIsNotNone(new)
            self.assertNotEqual(old.lease_id, new.lease_id)

            from v3.research_os_v3.event_delivery import EventDeliveryOwnershipError
            with self.assertRaises(EventDeliveryOwnershipError):
                delivery.ack("delivery-cross-1", old.lease_id)

            delivery.ack("delivery-cross-1", new.lease_id)


if __name__ == "__main__":
    unittest.main()
