import sqlite3
from pathlib import Path
import tempfile
import unittest

from research_os_v3.durable_events import DurableWorkflowEventStore
from research_os_v3.queue import DurableTaskQueue, QueueTask
from research_os_v3.runner import StatelessResearchRunner


class DurableWorkflowEventStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.path = Path(self.tempdir.name) / "events.db"

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_append_assigns_sequence_and_preserves_order(self) -> None:
        store = DurableWorkflowEventStore(self.path)
        first = store.append(
            "task.queued", workflow_id="workflow-1", task_id="task-1",
            correlation_id="corr-1", causation_id="root", producer="engine",
        )
        second = store.append(
            "task.started", workflow_id="workflow-1", task_id="task-1",
            correlation_id="corr-1", causation_id=first.event_id, producer="runner",
        )

        self.assertEqual(1, first.sequence)
        self.assertEqual(2, second.sequence)
        self.assertEqual(["task.queued", "task.started"], [item.event_type for item in store.list_events("workflow-1")])

    def test_duplicate_event_id_is_idempotent(self) -> None:
        store = DurableWorkflowEventStore(self.path)
        first = store.append(
            "task.queued", workflow_id="workflow-1", task_id="task-1",
            correlation_id="corr-1", causation_id="root", producer="engine",
            payload={"value": 1}, event_id="event-1",
        )
        duplicate = store.append(
            "task.changed", workflow_id="workflow-1", task_id="task-1",
            correlation_id="corr-1", causation_id="root", producer="other",
            payload={"value": 2}, event_id="event-1",
        )

        self.assertEqual(first, duplicate)
        self.assertEqual(1, len(store.list_events("workflow-1")))

    def test_events_survive_store_recreation(self) -> None:
        store = DurableWorkflowEventStore(self.path)
        event = store.append(
            "workflow.created", workflow_id="workflow-1", task_id="workflow",
            correlation_id="corr-1", causation_id="root", producer="engine",
        )
        restarted = DurableWorkflowEventStore(self.path)

        self.assertEqual(event, restarted.list_events("workflow-1")[0])

    def test_delivery_claim_suppresses_duplicate_consumer_delivery(self) -> None:
        store = DurableWorkflowEventStore(self.path)
        event = store.append(
            "task.succeeded", workflow_id="workflow-1", task_id="task-1",
            correlation_id="corr-1", causation_id="root", producer="runner",
        )

        self.assertTrue(store.claim_delivery(event.event_id, "consumer-a"))
        self.assertFalse(store.claim_delivery(event.event_id, "consumer-a"))
        self.assertTrue(store.claim_delivery(event.event_id, "consumer-b"))

    def test_runner_events_are_persisted_through_sink_adapter(self) -> None:
        store = DurableWorkflowEventStore(self.path)
        queue = DurableTaskQueue(Path(self.tempdir.name) / "queue.db")
        queue.enqueue(QueueTask("task-1", "research-1", {"input": "ok"}))
        runner = StatelessResearchRunner(
            queue,
            worker_id="worker-1",
            event_sink=store.event_sink(
                workflow_id="workflow-1", correlation_id="correlation-1"
            ),
        )

        result = runner.run_once(lambda task: None)
        restarted = DurableWorkflowEventStore(self.path)
        events = restarted.list_events("workflow-1", "task-1")

        self.assertEqual("completed", result.status)
        self.assertEqual([1, 2], [event.sequence for event in events])
        self.assertEqual("runner.claimed", events[0].event_type)
        self.assertEqual("runner.completed", events[1].event_type)

    def test_failed_delivery_can_be_retried_but_completed_delivery_cannot(self) -> None:
        store = DurableWorkflowEventStore(self.path)
        event = store.append(
            "task.succeeded", workflow_id="workflow-1", task_id="task-1",
            correlation_id="corr-1", causation_id="root", producer="runner",
        )

        self.assertTrue(store.claim_delivery(event.event_id, "consumer-a"))
        store.fail_delivery(event.event_id, "consumer-a", "temporary failure")
        self.assertTrue(store.claim_delivery(event.event_id, "consumer-a"))
        store.complete_delivery(event.event_id, "consumer-a")
        self.assertFalse(store.claim_delivery(event.event_id, "consumer-a"))

    def test_deliver_retries_after_consumer_failure(self) -> None:
        store = DurableWorkflowEventStore(self.path)
        event = store.append(
            "task.succeeded", workflow_id="workflow-1", task_id="task-1",
            correlation_id="corr-1", causation_id="root", producer="runner",
        )
        received = []

        with self.assertRaisesRegex(RuntimeError, "temporary"):
            store.deliver(event.event_id, "consumer-a", lambda item: (_ for _ in ()).throw(RuntimeError("temporary")))
        self.assertTrue(store.deliver(event.event_id, "consumer-a", received.append))
        self.assertEqual([event.event_id], [item.event_id for item in received])
        self.assertFalse(store.deliver(event.event_id, "consumer-a", received.append))

    def test_expired_delivery_lease_can_be_reclaimed(self) -> None:
        store = DurableWorkflowEventStore(self.path)
        event = store.append(
            "task.succeeded", workflow_id="workflow-1", task_id="task-1",
            correlation_id="corr-1", causation_id="root", producer="runner",
        )
        self.assertTrue(store.claim_delivery(event.event_id, "consumer-a", lease_seconds=1))
        with sqlite3.connect(self.path) as db:
            db.execute(
                "UPDATE event_deliveries SET lease_until=? WHERE event_id=?",
                ("2000-01-01T00:00:00+00:00", event.event_id),
            )
        self.assertTrue(store.claim_delivery(event.event_id, "consumer-b"))

    def test_reclaimed_delivery_rejects_stale_completion_token(self) -> None:
        store = DurableWorkflowEventStore(self.path)
        event = store.append(
            "task.succeeded", workflow_id="workflow-1", task_id="task-1",
            correlation_id="corr-1", causation_id="root", producer="runner",
        )
        first_token = store.claim_delivery_token(event.event_id, "consumer-a", lease_seconds=1)
        self.assertIsNotNone(first_token)
        with sqlite3.connect(self.path) as db:
            db.execute(
                "UPDATE event_deliveries SET lease_until=? WHERE event_id=?",
                ("2000-01-01T00:00:00+00:00", event.event_id),
            )
        second_token = store.claim_delivery_token(event.event_id, "consumer-a")
        self.assertIsNotNone(second_token)
        self.assertNotEqual(first_token, second_token)
        with self.assertRaisesRegex(ValueError, "actively claimed"):
            store.complete_delivery(event.event_id, "consumer-a", first_token)
        store.complete_delivery(event.event_id, "consumer-a", second_token)

    def test_restart_replay_flow_preserves_events_and_delivery_metrics(self) -> None:
        store = DurableWorkflowEventStore(self.path)
        event = store.append(
            "task.completed", workflow_id="workflow-e2e", task_id="task-1",
            correlation_id="corr-e2e", causation_id="root", producer="runner",
        )
        self.assertTrue(store.claim_delivery(event.event_id, "consumer-a"))
        store.fail_delivery(event.event_id, "consumer-a", "temporary")

        restarted = DurableWorkflowEventStore(self.path)
        received = []
        self.assertTrue(restarted.deliver(event.event_id, "consumer-a", received.append))
        self.assertFalse(restarted.deliver(event.event_id, "consumer-a", received.append))
        self.assertEqual(event, restarted.get_event(event.event_id))
        self.assertEqual(1, len(received))
        self.assertEqual(
            {
                "event_count": 1,
                "delivery_attempts": 2,
                "delivery_completed": 1,
            },
            restarted.metrics("workflow-e2e"),
        )


if __name__ == "__main__":
    unittest.main()
