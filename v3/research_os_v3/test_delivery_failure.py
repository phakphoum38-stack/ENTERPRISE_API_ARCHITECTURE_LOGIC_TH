import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from v3.dlq.models import DLQStatus
from v3.dlq.service import DLQService
from v3.dlq.sqlite_store import SQLiteDLQStore
from v3.research_os_v3.delivery_failure import DeliveryFailureCoordinator
from v3.research_os_v3.event_delivery import DurableEventDelivery, EventEnvelope


def event():
    return EventEnvelope(
        event_id="evt-failure-1", event_type="task.execute",
        occurred_at=datetime.now(timezone.utc).isoformat(),
        workflow_id="wf-1", task_id="task-1",
        correlation_id="corr-1", causation_id="cause-1",
        sequence=1, producer="test", payload={"task": "1"},
    )


class DeliveryFailureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.delivery = DurableEventDelivery(root / "events.db")
        self.delivery.append(event())
        self.delivery.register_delivery(
            event_id="evt-failure-1", consumer="worker",
            delivery_id="delivery-1", idempotency_key="idem-1", max_attempts=2,
        )
        self.dlq_store = SQLiteDLQStore(str(root / "dlq.db"))
        self.coordinator = DeliveryFailureCoordinator(
            self.delivery, DLQService(self.dlq_store),
        )

    def tearDown(self):
        self.dlq_store.close()
        self.tmp.cleanup()

    def test_retry_releases_lease_and_increments_attempt(self):
        claimed = self.delivery.claim("delivery-1")
        result = self.coordinator.fail(
            "delivery-1", claimed.lease_id, error=RuntimeError("transient")
        )
        self.assertEqual("available", result.status)
        self.assertEqual(2, result.attempt)
        self.assertIsNone(result.lease_id)
        self.assertIsNone(self.dlq_store.get("delivery-1"))

    def test_retry_exhaustion_persists_dlq_and_does_not_ack(self):
        first = self.delivery.claim("delivery-1")
        self.coordinator.fail("delivery-1", first.lease_id, error=RuntimeError("first"))
        second = self.delivery.claim("delivery-1")
        result = self.coordinator.fail(
            "delivery-1", second.lease_id, error=RuntimeError("terminal")
        )
        self.assertEqual("dlq", result.status)
        self.assertEqual(2, result.attempt)
        saved = self.dlq_store.get("delivery-1")
        self.assertIsNotNone(saved)
        self.assertEqual(DLQStatus.AVAILABLE, saved.status)
        self.assertEqual(2, saved.attempt)
        self.assertEqual("RuntimeError", saved.error_type)

    def test_non_retryable_failure_goes_directly_to_dlq(self):
        claimed = self.delivery.claim("delivery-1")
        result = self.coordinator.fail(
            "delivery-1", claimed.lease_id, error=ValueError("invalid"), retryable=False
        )
        self.assertEqual("dlq", result.status)
        saved = self.dlq_store.get("delivery-1")
        self.assertIsNotNone(saved)
        self.assertEqual(1, saved.attempt)
        self.assertEqual("ValueError", saved.error_type)

    def test_terminal_failure_is_idempotent_after_restart(self):
        claimed = self.delivery.claim("delivery-1")
        self.coordinator.fail(
            "delivery-1", claimed.lease_id, error=RuntimeError("terminal"), retryable=False
        )
        restarted = DurableEventDelivery(self.delivery.path)
        dlq = SQLiteDLQStore(str(self.tmp.name + "/dlq.db"))
        result = DeliveryFailureCoordinator(restarted, DLQService(dlq)).fail(
            "delivery-1", "ignored", error=RuntimeError("duplicate"), retryable=False
        )
        self.assertEqual("dlq", result.status)
        self.assertIsNotNone(dlq.get("delivery-1"))
        dlq.close()


if __name__ == "__main__":
    unittest.main()
