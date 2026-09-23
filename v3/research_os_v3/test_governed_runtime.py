from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from .event_delivery import EventEnvelope
from .governed_runtime import GovernedWorkflowRuntime
from .resource_lineage import ResourceConflictError, _sha256


class GovernedWorkflowRuntimeTests(unittest.TestCase):
    def test_retry_then_dlq_uses_one_delivery_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = GovernedWorkflowRuntime(Path(tmp), concurrency=1)
            event = EventEnvelope(
                event_id="event-1",
                event_type="workflow.task",
                occurred_at=datetime.now(timezone.utc).isoformat(),
                workflow_id="workflow-1",
                task_id="task-1",
                correlation_id="corr-1",
                causation_id="cause-1",
                sequence=1,
                producer="test",
                payload={"value": 1},
            )
            runtime.delivery.append(event)
            delivery = runtime.delivery.register_delivery(
                event_id=event.event_id,
                consumer="runner",
                delivery_id="delivery-1",
                idempotency_key="idem-1",
                max_attempts=2,
            )

            results = runtime.run([delivery.delivery_id], lambda _: (_ for _ in ()).throw(RuntimeError("boom")))
            self.assertEqual(results[0].status, "failed")
            self.assertEqual(runtime.delivery.get_delivery("delivery-1").status, "available")

            runtime.run([delivery.delivery_id], lambda _: (_ for _ in ()).throw(RuntimeError("boom")))
            final = runtime.delivery.get_delivery("delivery-1")
            self.assertEqual(final.status, "dlq")
            record = runtime.dlq_store.get("delivery-1")
            self.assertIsNotNone(record)
            self.assertEqual(record.attempt, 2)

            runtime.close()

    def test_stale_update_releases_and_reconciles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = GovernedWorkflowRuntime(Path(tmp))
            initial = runtime.lineage.initialize("file-1", {"version": 1})
            released = []
            reconciled = []

            runtime.lineage.update(
                "file-1",
                expected_version=initial.version,
                expected_sha256=initial.content_sha256,
                content={"version": 2},
                release_resources=lambda: released.append(True),
                reconcile_delivery=lambda evidence: reconciled.append(evidence.conflict_id),
            )
            with self.assertRaises(ResourceConflictError):
                runtime.update_resource(
                    "file-1",
                    expected_version=initial.version,
                    expected_sha256=initial.content_sha256,
                    content={"version": "stale"},
                    release_resources=lambda: released.append(True),
                    reconcile_delivery=lambda evidence: reconciled.append(evidence.conflict_id),
                )

            self.assertEqual(released, [True])
            self.assertEqual(len(reconciled), 1)
            self.assertEqual(runtime.lineage.head("file-1").content_sha256, _sha256({"version": 2}))
            runtime.close()
