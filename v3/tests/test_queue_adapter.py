import unittest

from v3.dlq.models import DLQRecord
from v3.dlq.queue_adapter import DLQReplayQueueAdapter


class FakeExistingQueue:
    def __init__(self):
        self.items = []

    def enqueue(self, record):
        self.items.append(record)


def make_record():
    return DLQRecord(
        task_id="task-queue-1",
        event_id="event-queue-1",
        delivery_id="delivery-queue-1",
        idempotency_key="idem-queue-1",
        attempt=3,
        max_attempts=3,
        error_type="RuntimeError",
        error_message="failed",
        payload_reference="payload://queue-1",
    )


class QueueAdapterTests(unittest.TestCase):
    def test_replay_uses_existing_queue_boundary(self):
        existing_queue = FakeExistingQueue()
        adapter = DLQReplayQueueAdapter(existing_queue)
        record = make_record()

        adapter.enqueue(record)

        self.assertEqual([record], existing_queue.items)

    def test_adapter_does_not_create_second_queue(self):
        existing_queue = FakeExistingQueue()
        adapter = DLQReplayQueueAdapter(existing_queue)
        self.assertIs(existing_queue, adapter._queue)


if __name__ == "__main__":
    unittest.main()
