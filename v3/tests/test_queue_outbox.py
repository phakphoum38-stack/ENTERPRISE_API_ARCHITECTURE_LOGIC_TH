from pathlib import Path
import tempfile
import unittest

from research_os_v3.durable_events import DurableWorkflowEventStore
from research_os_v3.queue import DurableTaskQueue, QueueTask
from research_os_v3.workflow_projection import WorkflowStateProjector


class QueueOutboxTests(unittest.TestCase):
    def test_state_changes_write_transactional_outbox_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            queue = DurableTaskQueue(Path(tmp) / "queue.db")
            queue.enqueue(QueueTask("task-1", "research-1", {"value": 1}))
            claimed = queue.claim(worker_id="worker-1")
            assert claimed is not None and claimed.lease_id is not None
            queue.ack(claimed.task_id, claimed.lease_id)

            events = queue.outbox_events()
            self.assertEqual(
                ["task.queued", "task.started", "task.succeeded"],
                [event.event_type for event in events],
            )
            queue.mark_outbox_published(events[0].event_id)
            self.assertEqual(2, len(queue.outbox_events()))
            self.assertEqual(3, len(queue.outbox_events(include_published=True)))

    def test_outbox_publisher_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            queue = DurableTaskQueue(Path(tmp) / "queue.db")
            events = DurableWorkflowEventStore(Path(tmp) / "events.db")
            queue.enqueue(QueueTask("task-1", "research-1", {"value": 1}))

            self.assertEqual(1, queue.publish_outbox(events, workflow_id="workflow-1", correlation_id="corr-1"))
            self.assertEqual(0, queue.publish_outbox(events, workflow_id="workflow-1", correlation_id="corr-1"))
            self.assertEqual(["task.queued"], [event.event_type for event in events.list_events("workflow-1")])

    def test_queue_outbox_projects_into_workflow_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            queue = DurableTaskQueue(Path(tmp) / "queue.db")
            events = DurableWorkflowEventStore(Path(tmp) / "events.db")
            projection = WorkflowStateProjector(Path(tmp) / "projection.db")
            queue.enqueue(QueueTask("task-1", "research-1", {"value": 1}))
            claimed = queue.claim(worker_id="worker-1")
            assert claimed is not None and claimed.lease_id is not None
            queue.ack(claimed.task_id, claimed.lease_id)

            queue.publish_outbox(events, workflow_id="workflow-1", correlation_id="corr-1")
            for event in events.list_events("workflow-1", "task-1"):
                projection.apply(event)

            projected = projection.get("workflow-1", "task-1")
            assert projected is not None
            self.assertEqual("SUCCEEDED", projected.state)
            self.assertEqual(3, projected.sequence)

    def test_failed_publish_keeps_outbox_pending_for_idempotent_retry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            queue = DurableTaskQueue(Path(tmp) / "queue.db")
            events = DurableWorkflowEventStore(Path(tmp) / "events.db")
            queue.enqueue(QueueTask("task-1", "research-1", {"value": 1}))

            class FlakyStore:
                def __init__(self, target):
                    self.target = target
                    self.failed = False

                def append(self, *args, **kwargs):
                    if not self.failed:
                        self.failed = True
                        raise RuntimeError("event store unavailable")
                    return self.target.append(*args, **kwargs)

            flaky = FlakyStore(events)
            with self.assertRaisesRegex(RuntimeError, "unavailable"):
                queue.publish_outbox(flaky, workflow_id="workflow-1", correlation_id="corr-1")
            self.assertEqual(1, len(queue.outbox_events()))
            self.assertEqual(1, queue.publish_outbox(flaky, workflow_id="workflow-1", correlation_id="corr-1"))
            self.assertEqual(1, len(events.list_events("workflow-1")))

    def test_drain_outbox_isolates_failures_and_leaves_them_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            queue = DurableTaskQueue(Path(tmp) / "queue.db")
            events = DurableWorkflowEventStore(Path(tmp) / "events.db")
            queue.enqueue(QueueTask("task-1", "research-1", {"value": 1}))
            queue.enqueue(QueueTask("task-2", "research-1", {"value": 2}))

            class SelectiveStore:
                def __init__(self, target):
                    self.target = target

                def append(self, event_type, **kwargs):
                    if kwargs["task_id"] == "task-1":
                        raise RuntimeError("task unavailable")
                    return self.target.append(event_type, **kwargs)

            result = queue.drain_outbox(
                SelectiveStore(events), workflow_id="workflow-1", correlation_id="corr-1"
            )
            self.assertEqual({"published": 1, "failed": 1}, result)
            self.assertEqual(1, len(queue.outbox_events()))
            self.assertEqual(["task.queued"], [item.event_type for item in events.list_events("workflow-1")])


if __name__ == "__main__":
    unittest.main()
