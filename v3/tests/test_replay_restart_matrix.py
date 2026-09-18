from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from v3.research_os_v3.event_delivery import DurableEventDelivery, EventEnvelope


class ReplayRestartMatrixTests(unittest.TestCase):
    def test_repeated_restart_recovery_preserves_one_delivery_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.db"
            event = EventEnvelope(
                event_id="evt-restart-1",
                event_type="task.completed",
                occurred_at="2026-09-18T00:00:00+00:00",
                workflow_id="wf-restart-1",
                task_id="task-restart-1",
                correlation_id="corr-restart-1",
                causation_id="cause-restart-1",
                sequence=1,
                producer="worker-a",
                payload={"ok": True},
            )
            ledger = DurableEventDelivery(path, lease_seconds=30)
            ledger.append(event)
            ledger.register_delivery(
                event_id=event.event_id,
                consumer="consumer-a",
                delivery_id="delivery-restart-1",
                idempotency_key="idem-restart-1",
            )

            original = ledger.claim("delivery-restart-1")
            self.assertIsNotNone(original)

            import sqlite3
            with sqlite3.connect(path) as db:
                db.execute(
                    "UPDATE deliveries SET lease_until=? WHERE delivery_id=?",
                    ("2000-01-01T00:00:00+00:00", "delivery-restart-1"),
                )

            for _ in range(3):
                restarted = DurableEventDelivery(path, lease_seconds=30)
                self.assertEqual(1, restarted.recover_expired())
                replacement = restarted.claim("delivery-restart-1")
                self.assertIsNotNone(replacement)
                with sqlite3.connect(path) as db:
                    db.execute(
                        "UPDATE deliveries SET lease_until=? WHERE delivery_id=?",
                        ("2000-01-01T00:00:00+00:00", "delivery-restart-1"),
                    )

            final = DurableEventDelivery(path, lease_seconds=30)
            self.assertEqual(1, final.recover_expired())
            owner = final.claim("delivery-restart-1")
            self.assertIsNotNone(owner)
            final.ack(owner.delivery_id, owner.lease_id)
            self.assertEqual("acked", final.get_delivery(owner.delivery_id).status)

            # The durable identity remains one delivery row after repeated recovery.
            with sqlite3.connect(path) as db:
                count = db.execute(
                    "SELECT COUNT(*) FROM deliveries WHERE idempotency_key=?",
                    ("idem-restart-1",),
                ).fetchone()[0]
            self.assertEqual(1, count)


if __name__ == "__main__":
    unittest.main()
