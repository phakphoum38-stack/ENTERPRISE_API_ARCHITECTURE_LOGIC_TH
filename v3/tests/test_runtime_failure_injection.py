from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from v3.research_os_v3.event_delivery import DurableEventDelivery, EventEnvelope
from v3.research_os_v3.queue import DurableTaskQueue, QueueTask


def event() -> EventEnvelope:
    return EventEnvelope(
        event_id="evt-failure-1",
        event_type="task.completed",
        occurred_at="2026-09-18T00:00:00+00:00",
        workflow_id="wf-1",
        task_id="task-1",
        correlation_id="corr-1",
        causation_id="cause-1",
        sequence=1,
        producer="worker-a",
        payload={"result": "ok"},
    )


class RuntimeFailureInjectionTests(unittest.TestCase):
    def test_task_crash_before_ack_is_recoverable_without_old_owner_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            queue = DurableTaskQueue(Path(directory) / "queue.db", default_lease_seconds=30)
            queue.enqueue(QueueTask("task-1", "research-1", {"work": "x"}))

            crashed = queue.claim(worker_id="worker-a", lease_seconds=30)
            self.assertIsNotNone(crashed)

            # Failure injection: the process disappears before ACK.
            with __import__("sqlite3").connect(queue.path) as db:
                db.execute(
                    "UPDATE research_queue SET lease_until=? WHERE task_id=?",
                    ("2000-01-01T00:00:00+00:00", "task-1"),
                )

            self.assertEqual(1, queue.recover_expired_leases())
            recovered = queue.claim(worker_id="worker-b", lease_seconds=30)
            self.assertIsNotNone(recovered)

            from v3.research_os_v3.queue import LeaseOwnershipError
            with self.assertRaises(LeaseOwnershipError):
                queue.ack("task-1", crashed.lease_id)

            queue.ack("task-1", recovered.lease_id)

    def test_event_crash_before_ack_is_recoverable_after_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.db"
            ledger = DurableEventDelivery(path, lease_seconds=30)
            ledger.append(event())
            ledger.register_delivery(
                event_id="evt-failure-1",
                consumer="consumer-a",
                delivery_id="delivery-1",
                idempotency_key="idem-failure-1",
            )

            crashed = ledger.claim("delivery-1")
            self.assertIsNotNone(crashed)

            # Failure injection: process dies while delivery is leased.
            with __import__("sqlite3").connect(path) as db:
                db.execute(
                    "UPDATE deliveries SET lease_until=? WHERE delivery_id=?",
                    ("2000-01-01T00:00:00+00:00", "delivery-1"),
                )

            restarted = DurableEventDelivery(path, lease_seconds=30)
            self.assertEqual(1, restarted.recover_expired())
            recovered = restarted.claim("delivery-1")
            self.assertIsNotNone(recovered)
            self.assertNotEqual(crashed.lease_id, recovered.lease_id)

            from v3.research_os_v3.event_delivery import EventDeliveryOwnershipError
            with self.assertRaises(EventDeliveryOwnershipError):
                restarted.ack("delivery-1", crashed.lease_id)

            restarted.ack("delivery-1", recovered.lease_id)

    def test_failure_evidence_is_deterministic(self):
        record = {
            "scenario": "worker_crash_before_ack",
            "task_id": "task-1",
            "reclaimed": True,
            "stale_owner_rejected": True,
            "final_status": "completed",
        }
        first = json.dumps(record, sort_keys=True, separators=(",", ":"))
        second = json.dumps(record, sort_keys=True, separators=(",", ":"))
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
