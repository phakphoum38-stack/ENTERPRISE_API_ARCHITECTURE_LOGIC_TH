import threading
import unittest

from v3.dlq.idempotency import IdempotencyRegistry
from v3.dlq.models import DLQRecord, DLQStatus
from v3.dlq.queue_adapter import DLQReplayQueueAdapter
from v3.dlq.replay import ReplayAdapter
from v3.dlq.service import DLQService
from v3.dlq.store import InMemoryDLQStore


class FakeQueue:
    def __init__(self):
        self.items = []
        self.lock = threading.Lock()

    def enqueue(self, record):
        with self.lock:
            self.items.append(record)


def make_record():
    return DLQRecord(
        task_id="task-integration-1",
        event_id="event-integration-1",
        delivery_id="delivery-integration-1",
        idempotency_key="idem-integration-1",
        attempt=3,
        max_attempts=3,
        error_type="RuntimeError",
        error_message="worker failed",
        payload_reference="payload://integration-1",
    )


class ReplayIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.store = InMemoryDLQStore()
        self.service = DLQService(self.store)
        self.registry = IdempotencyRegistry()
        self.replay = ReplayAdapter(self.service, self.registry)
        self.queue = FakeQueue()
        self.adapter = DLQReplayQueueAdapter(self.queue)
        self.service.dead_letter(make_record())

    def test_replay_reaches_existing_queue(self):
        result = self.replay.replay("task-integration-1", self.adapter.enqueue)
        self.assertEqual(DLQStatus.REPLAYED, result.status)
        self.assertEqual(1, len(self.queue.items))
        self.assertEqual("task-integration-1", self.queue.items[0].task_id)

    def test_duplicate_replay_does_not_enqueue_twice(self):
        self.replay.replay("task-integration-1", self.adapter.enqueue)
        with self.assertRaises(ValueError):
            self.replay.replay("task-integration-1", self.adapter.enqueue)
        self.assertEqual(1, len(self.queue.items))

    def test_concurrent_replay_allows_only_one_delivery(self):
        barrier = threading.Barrier(2)
        results = []
        errors = []

        def run():
            barrier.wait()
            try:
                results.append(self.replay.replay("task-integration-1", self.adapter.enqueue))
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=run) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(1, len(results))
        self.assertEqual(1, len(self.queue.items))
        self.assertTrue(any(isinstance(error, ValueError) for error in errors))

    def test_enqueue_failure_releases_idempotency_key(self):
        def fail(_):
            raise RuntimeError("queue unavailable")

        with self.assertRaisesRegex(RuntimeError, "queue unavailable"):
            self.replay.replay("task-integration-1", fail)

        self.assertEqual(DLQStatus.REPLAYING, self.store.get("task-integration-1").status)
        self.assertFalse(self.registry.is_claimed("idem-integration-1"))


if __name__ == "__main__":
    unittest.main()
