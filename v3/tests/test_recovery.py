import os
import tempfile
import unittest

from v3.dlq.models import DLQRecord, DLQStatus
from v3.dlq.recovery import DLQRecoveryManager
from v3.dlq.sqlite_store import SQLiteDLQStore


def make_record(task_id="task-recovery-1"):
    return DLQRecord(
        task_id=task_id,
        event_id="event-recovery-1",
        delivery_id="delivery-recovery-1",
        idempotency_key="idem-recovery-1",
        attempt=3,
        max_attempts=3,
        error_type="RuntimeError",
        error_message="worker crashed",
        payload_reference="payload://recovery-1",
    )


class RecoveryTests(unittest.TestCase):
    def test_crash_recovery_resets_persisted_replaying_state(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        try:
            first = SQLiteDLQStore(path)
            first.put(make_record())
            first.mark_replaying("task-recovery-1")
            first.close()

            restarted = SQLiteDLQStore(path)
            manager = DLQRecoveryManager(restarted)
            self.assertEqual(["task-recovery-1"], manager.recover())
            self.assertEqual(DLQStatus.AVAILABLE, restarted.get("task-recovery-1").status)
            self.assertEqual([], restarted.recover_replaying())
            restarted.close()
        finally:
            os.unlink(path)

    def test_recovery_does_not_execute_or_enqueue(self):
        store = SQLiteDLQStore()
        store.put(make_record())
        store.mark_replaying("task-recovery-1")
        manager = DLQRecoveryManager(store)
        recovered = manager.recover()
        self.assertEqual(["task-recovery-1"], recovered)
        self.assertEqual(DLQStatus.AVAILABLE, store.get("task-recovery-1").status)
        store.close()


if __name__ == "__main__":
    unittest.main()
