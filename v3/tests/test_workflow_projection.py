from pathlib import Path
import tempfile
import unittest

from research_os_v3.durable_events import DurableWorkflowEventStore
from research_os_v3.workflow_projection import WorkflowStateProjector


class WorkflowStateProjectorTests(unittest.TestCase):
    def test_projection_is_idempotent_and_survives_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            events = DurableWorkflowEventStore(Path(tmp) / "events.db")
            projection = WorkflowStateProjector(Path(tmp) / "projection.db")
            queued = events.append(
                "task.queued", workflow_id="workflow-1", task_id="task-1",
                correlation_id="corr-1", causation_id="root", producer="queue",
            )
            succeeded = events.append(
                "task.succeeded", workflow_id="workflow-1", task_id="task-1",
                correlation_id="corr-1", causation_id=queued.event_id, producer="runner",
            )

            self.assertTrue(projection.apply(queued))
            self.assertTrue(projection.apply(succeeded))
            self.assertFalse(projection.apply(succeeded))
            restarted = WorkflowStateProjector(Path(tmp) / "projection.db")
            projected = restarted.get("workflow-1", "task-1")
            assert projected is not None
            self.assertEqual("SUCCEEDED", projected.state)
            self.assertEqual(2, projected.sequence)

    def test_terminal_state_rejects_later_transition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            events = DurableWorkflowEventStore(Path(tmp) / "events.db")
            projection = WorkflowStateProjector(Path(tmp) / "projection.db")
            succeeded = events.append(
                "task.succeeded", workflow_id="workflow-1", task_id="task-1",
                correlation_id="corr-1", causation_id="root", producer="runner",
            )
            later = events.append(
                "task.started", workflow_id="workflow-1", task_id="task-1",
                correlation_id="corr-1", causation_id=succeeded.event_id, producer="runner",
            )
            projection.apply(succeeded)
            with self.assertRaisesRegex(ValueError, "terminal"):
                projection.apply(later)


if __name__ == "__main__":
    unittest.main()
