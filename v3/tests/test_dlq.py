import unittest

from v3.dlq.models import DLQRecord, DLQStatus
from v3.dlq.service import DLQService
from v3.dlq.store import InMemoryDLQStore


def record(task_id="task-1", key="idem-1"):
    return DLQRecord(
        task_id=task_id,
        event_id="event-1",
        delivery_id="delivery-1",
        idempotency_key=key,
        attempt=3,
        max_attempts=3,
        error_type="RuntimeError",
        error_message="boom",
        payload_reference="payload://task-1",
    )


class DLQServiceTests(unittest.TestCase):
    def setUp(self):
        self.store = InMemoryDLQStore()
        self.service = DLQService(self.store)

    def test_dead_letter_persists_available_record(self):
        self.service.dead_letter(record())
        saved = self.store.get("task-1")
        self.assertIsNotNone(saved)
        self.assertEqual(saved.status, DLQStatus.AVAILABLE)

    def test_replay_enqueues_once_and_marks_replayed(self):
        self.service.dead_letter(record())
        enqueued = []
        result = self.service.replay("task-1", enqueued.append)
        self.assertEqual(["task-1"], [item.task_id for item in enqueued])
        self.assertEqual(DLQStatus.REPLAYED, result.status)
        self.assertEqual(1, result.replay_count)

    def test_duplicate_replay_is_rejected(self):
        self.service.dead_letter(record())
        self.service.replay("task-1", lambda _: None)
        with self.assertRaises(ValueError):
            self.service.replay("task-1", lambda _: None)

    def test_failed_replay_is_not_marked_replayed(self):
        self.service.dead_letter(record())
        with self.assertRaisesRegex(RuntimeError, "enqueue failed"):
            self.service.replay("task-1", lambda _: (_ for _ in ()).throw(RuntimeError("enqueue failed")))
        self.assertEqual(DLQStatus.REPLAYING, self.store.get("task-1").status)

    def test_duplicate_task_cannot_be_inserted(self):
        self.service.dead_letter(record())
        with self.assertRaises(ValueError):
            self.service.dead_letter(record())


if __name__ == "__main__":
    unittest.main()
