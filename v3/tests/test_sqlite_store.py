import os
import tempfile
import unittest

from v3.dlq.models import DLQRecord, DLQStatus
from v3.dlq.sqlite_store import SQLiteDLQStore


def make_record():
    return DLQRecord(
        task_id="task-durable-1",
        event_id="event-durable-1",
        delivery_id="delivery-durable-1",
        idempotency_key="idem-durable-1",
        attempt=3,
        max_attempts=3,
        error_type="RuntimeError",
        error_message="worker failed",
        payload_reference="payload://durable-1",
    )


class SQLiteDLQStoreTests(unittest.TestCase):
    def test_record_survives_store_recreation(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        try:
            store = SQLiteDLQStore(path)
            store.put(make_record())
            store.mark_replaying("task-durable-1")
            store.close()

            restarted = SQLiteDLQStore(path)
            record = restarted.get("task-durable-1")
            self.assertIsNotNone(record)
            self.assertEqual(DLQStatus.REPLAYING, record.status)
            restarted.close()
        finally:
            os.unlink(path)

    def test_replaying_records_are_recoverable(self):
        store = SQLiteDLQStore()
        store.put(make_record())
        store.mark_replaying("task-durable-1")
        recovered = store.recover_replaying()
        self.assertEqual(["task-durable-1"], [record.task_id for record in recovered])
        store.close()

    def test_reset_replaying_returns_record_to_available(self):
        store = SQLiteDLQStore()
        store.put(make_record())
        store.mark_replaying("task-durable-1")
        record = store.reset_replaying("task-durable-1")
        self.assertEqual(DLQStatus.AVAILABLE, record.status)
        store.close()


if __name__ == "__main__":
    unittest.main()
