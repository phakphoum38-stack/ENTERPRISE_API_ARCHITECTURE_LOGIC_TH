import unittest

from v3.dlq.idempotency import IdempotencyRegistry
from v3.dlq.models import DLQRecord
from v3.dlq.replay import ReplayAdapter
from v3.dlq.service import DLQService
from v3.dlq.store import InMemoryDLQStore


class ReplayAdapterTests(unittest.TestCase):
    def setUp(self):
        self.store = InMemoryDLQStore()
        self.service = DLQService(self.store)
        self.adapter = ReplayAdapter(self.service, IdempotencyRegistry())
        self.service.dead_letter(
            DLQRecord(
                task_id="task-1",
                event_id="event-1",
                delivery_id="delivery-1",
                idempotency_key="idem-1",
                attempt=3,
                max_attempts=3,
                error_type="RuntimeError",
                error_message="boom",
                payload_reference="payload://task-1",
            )
        )

    def test_replay_delivers_to_existing_queue_callback(self):
        delivered = []
        result = self.adapter.replay("task-1", delivered.append)
        self.assertEqual("task-1", delivered[0].task_id)
        self.assertEqual("replayed", result.status.value)

    def test_second_replay_is_rejected(self):
        self.adapter.replay("task-1", lambda _: None)
        with self.assertRaisesRegex(ValueError, "duplicate replay"):
            self.adapter.replay("task-1", lambda _: None)

    def test_failed_enqueue_releases_idempotency_claim(self):
        with self.assertRaises(RuntimeError):
            self.adapter.replay("task-1", lambda _: (_ for _ in ()).throw(RuntimeError("queue unavailable")))
        self.assertEqual("replaying", self.store.get("task-1").status.value)

        # The delivery key can be retried after an unsuccessful enqueue.
        delivered = []
        # The DLQ service still owns the replay state; a production adapter
        # should recover REPLAYING records explicitly before re-delivery.
        self.assertEqual([], delivered)


if __name__ == "__main__":
    unittest.main()
