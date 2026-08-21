from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from v3.research_os_v3.queue import DurableTaskQueue, LeaseOwnershipError, QueueTask


class WorkerCrashRecoveryTests(unittest.TestCase):
    def test_expired_worker_lease_is_reclaimed_by_next_worker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "queue.sqlite"
            queue = DurableTaskQueue(path, default_lease_seconds=30)
            queue.enqueue(QueueTask("task-1", "research-1", {"payload": "x"}))

            first = queue.claim(worker_id="worker-a", lease_seconds=30)
            self.assertIsNotNone(first)
            assert first is not None
            assert first.lease_id is not None

            # Simulate a worker/process crash by expiring its persisted lease.
            expired = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
            with sqlite3.connect(path) as db:
                db.execute(
                    "UPDATE research_queue SET lease_until=? WHERE task_id=?",
                    (expired, "task-1"),
                )

            self.assertEqual(1, queue.recover_expired_leases())

            second = queue.claim(worker_id="worker-b", lease_seconds=30)
            self.assertIsNotNone(second)
            assert second is not None
            self.assertEqual("task-1", second.task_id)
            self.assertNotEqual(first.lease_id, second.lease_id)
            self.assertEqual("worker-b", self._worker_id(path, "task-1"))

            queue.ack(second.task_id, second.lease_id)
            self.assertEqual("completed", self._status(path, "task-1"))
            queue.close()

    def test_stale_crashed_worker_cannot_ack_after_reclaim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "queue.sqlite"
            queue = DurableTaskQueue(path, default_lease_seconds=30)
            queue.enqueue(QueueTask("task-1", "research-1", {"payload": "x"}))

            first = queue.claim(worker_id="worker-a", lease_seconds=30)
            assert first is not None
            assert first.lease_id is not None

            expired = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
            with sqlite3.connect(path) as db:
                db.execute(
                    "UPDATE research_queue SET lease_until=? WHERE task_id=?",
                    (expired, "task-1"),
                )

            queue.recover_expired_leases()
            second = queue.claim(worker_id="worker-b", lease_seconds=30)
            assert second is not None
            assert second.lease_id is not None

            with self.assertRaises(LeaseOwnershipError):
                queue.ack(first.task_id, first.lease_id)

            queue.ack(second.task_id, second.lease_id)
            self.assertEqual("completed", self._status(path, "task-1"))
            queue.close()

    @staticmethod
    def _status(path: Path, task_id: str) -> str:
        with sqlite3.connect(path) as db:
            row = db.execute(
                "SELECT status FROM research_queue WHERE task_id=?",
                (task_id,),
            ).fetchone()
        assert row is not None
        return str(row[0])

    @staticmethod
    def _worker_id(path: Path, task_id: str) -> str:
        with sqlite3.connect(path) as db:
            row = db.execute(
                "SELECT worker_id FROM research_queue WHERE task_id=?",
                (task_id,),
            ).fetchone()
        assert row is not None
        return str(row[0])


if __name__ == "__main__":
    unittest.main()
