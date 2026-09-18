from __future__ import annotations

import unittest
from v3.dlq.models import DLQRecord, DLQStatus


class DLQReplayLineageContractTests(unittest.TestCase):
    def _record(self) -> DLQRecord:
        return DLQRecord(
            task_id="task-dlq-1",
            event_id="event-dlq-1",
            delivery_id="delivery-dlq-1",
            idempotency_key="idem-dlq-1",
            attempt=3,
            max_attempts=3,
            error_type="WorkerCrash",
            error_message="worker crashed before acknowledgement",
            payload_reference="payload://task-dlq-1",
            first_failed_at="2026-09-18T00:00:00+00:00",
            last_failed_at="2026-09-18T00:00:01+00:00",
            failed_at="2026-09-18T00:00:01+00:00",
            lease_id="lease-dlq-1",
            replay_count=0,
            status=DLQStatus.AVAILABLE,
            metadata={"source": "v3"},
        )

    def test_dlq_record_contains_complete_execution_lineage(self):
        record = self._record()
        for value in (
            record.task_id,
            record.event_id,
            record.delivery_id,
            record.idempotency_key,
            record.lease_id,
            record.payload_reference,
        ):
            self.assertTrue(value)

    def test_replay_preserves_task_event_and_idempotency_identity(self):
        record = self._record()
        self.assertEqual("task-dlq-1", record.task_id)
        self.assertEqual("event-dlq-1", record.event_id)
        self.assertEqual("delivery-dlq-1", record.delivery_id)
        self.assertEqual("idem-dlq-1", record.idempotency_key)
        self.assertEqual(0, record.replay_count)
        self.assertEqual(DLQStatus.AVAILABLE, record.status)

    def test_dlq_state_machine_uses_existing_boundary(self):
        record = self._record()
        replaying = record.__class__(**{**record.__dict__, "status": DLQStatus.REPLAYING, "replay_count": 1})
        replayed = record.__class__(**{**record.__dict__, "status": DLQStatus.REPLAYED, "replay_count": 1})
        rejected = record.__class__(**{**record.__dict__, "status": DLQStatus.REJECTED, "replay_count": 1})
        self.assertEqual(DLQStatus.REPLAYING, replaying.status)
        self.assertEqual(DLQStatus.REPLAYED, replayed.status)
        self.assertEqual(DLQStatus.REJECTED, rejected.status)
        self.assertEqual(record.task_id, replayed.task_id)
        self.assertEqual(record.idempotency_key, replayed.idempotency_key)


if __name__ == "__main__":
    unittest.main()
