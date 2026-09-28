from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path

from v3.research_os_v3.queue import DurableTaskQueue, LeaseOwnershipError, QueueTask


class QueueLeaseFencingTests(unittest.TestCase):
    def test_stale_lease_cannot_ack_retry_or_fail_after_reclaim(self):
        path = Path(self.id().replace(".", "_") + ".db")
        try:
            queue = DurableTaskQueue(path, default_lease_seconds=30)
            queue.enqueue(QueueTask("task-1", "research-1", {"value": 1}))
            first = queue.claim(worker_id="worker-a", lease_seconds=30)
            self.assertIsNotNone(first)
            self.assertIsNotNone(first.lease_id)

            with sqlite3.connect(path) as db:
                db.execute(
                    "UPDATE research_queue SET lease_until=? WHERE task_id=?",
                    ("2000-01-01T00:00:00+00:00", "task-1"),
                )

            self.assertEqual(1, queue.recover_expired_leases())
            second = queue.claim(worker_id="worker-b", lease_seconds=30)
            self.assertIsNotNone(second)
            self.assertNotEqual(first.lease_id, second.lease_id)

            for operation in (
                lambda: queue.ack("task-1", first.lease_id),
                lambda: queue.retry("task-1", first.lease_id),
                lambda: queue.fail("task-1", first.lease_id),
            ):
                with self.assertRaises(LeaseOwnershipError):
                    operation()

            queue.ack("task-1", second.lease_id)
        finally:
            path.unlink(missing_ok=True)

    def test_active_owner_can_renew_and_complete(self):
        path = Path(self.id().replace(".", "_") + ".db")
        try:
            queue = DurableTaskQueue(path, default_lease_seconds=30)
            queue.enqueue(QueueTask("task-1", "research-1", {"value": 1}))
            claimed = queue.claim(worker_id="worker-a", lease_seconds=30)
            self.assertIsNotNone(claimed)
            renewed = queue.renew_lease("task-1", claimed.lease_id, lease_seconds=30)
            self.assertEqual(claimed.lease_id, renewed.lease_id)
            queue.ack("task-1", renewed.lease_id)
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
