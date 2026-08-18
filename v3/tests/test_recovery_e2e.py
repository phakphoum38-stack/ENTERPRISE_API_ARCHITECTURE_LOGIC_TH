import os
import tempfile
import unittest

from v3.dlq.models import DLQRecord, DLQStatus
from v3.dlq.queue_adapter import DLQReplayQueueAdapter
from v3.dlq.recovery import DLQRecoveryManager
from v3.dlq.sqlite_store import SQLiteDLQStore


class ExistingWorkerPool:
    """Minimal test double for the existing worker-pool queue boundary."""

    def __init__(self):
        self.enqueued = []
        self.executed = []

    def enqueue(self, record):
        self.enqueued.append(record)

    def run_once(self):
        if self.enqueued:
            self.executed.append(self.enqueued.pop(0))


def make_record():
    return DLQRecord(
        task_id="task-e2e-recovery",
        event_id="event-e2e-recovery",
        delivery_id="delivery-e2e-recovery",
        idempotency_key="idem-e2e-recovery",
        attempt=3,
        max_attempts=3,
        error_type="RuntimeError",
        error_message="worker crashed",
        payload_reference="payload://e2e-recovery",
    )


class RecoveryE2ETests(unittest.TestCase):
    def test_restart_recovery_returns_task_to_existing_queue_and_worker(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        try:
            first = SQLiteDLQStore(path)
            first.put(make_record())
            first.mark_replaying("task-e2e-recovery")
            first.close()  # simulated process crash/restart boundary

            restarted = SQLiteDLQStore(path)
            manager = DLQRecoveryManager(restarted)
            self.assertEqual(["task-e2e-recovery"], manager.recover())
            self.assertEqual(DLQStatus.AVAILABLE, restarted.get("task-e2e-recovery").status)

            worker_pool = ExistingWorkerPool()
            queue = DLQReplayQueueAdapter(worker_pool)
            recovered = restarted.get("task-e2e-recovery")
            queue.enqueue(recovered)
            self.assertEqual(1, len(worker_pool.enqueued))

            worker_pool.run_once()
            self.assertEqual(1, len(worker_pool.executed))
            self.assertEqual("task-e2e-recovery", worker_pool.executed[0].task_id)
            restarted.close()
        finally:
            os.unlink(path)

    def test_recovery_does_not_duplicate_worker_delivery(self):
        store = SQLiteDLQStore()
        store.put(make_record())
        store.mark_replaying("task-e2e-recovery")
        manager = DLQRecoveryManager(store)
        manager.recover()

        worker_pool = ExistingWorkerPool()
        queue = DLQReplayQueueAdapter(worker_pool)
        record = store.get("task-e2e-recovery")
        queue.enqueue(record)
        worker_pool.run_once()

        self.assertEqual(1, len(worker_pool.executed))
        self.assertEqual([], worker_pool.enqueued)
        store.close()


if __name__ == "__main__":
    unittest.main()
