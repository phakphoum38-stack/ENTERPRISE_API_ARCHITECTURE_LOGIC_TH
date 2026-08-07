import os
import tempfile
import unittest
from unittest.mock import patch

from agent_runtime import AgentEventBus, AgentTaskQueue, SharedContextStore


class AgentRuntimeTest(unittest.TestCase):
    def _runtime(self, tmp: str) -> AgentTaskQueue:
        return AgentTaskQueue(
            event_bus=AgentEventBus(),
            context_store=SharedContextStore(tmp),
        )

    def test_read_only_task_routes_and_completes(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"RESEARCH_OS_DATA_DIR": tmp}, clear=False):
            runtime = self._runtime(tmp)
            task = runtime.submit("review github repository workflow")
            self.assertEqual(task["selected_agent"], "github")
            self.assertEqual(task["status"], "completed")
            self.assertEqual(task["result"]["execution"], "runtime_ready")
            events = runtime.events.list(task_id=task["task_id"])
            self.assertEqual([event["event_type"] for event in events], ["task.queued", "task.started", "task.completed"])

    def test_write_capable_task_waits_for_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self._runtime(tmp)
            task = runtime.submit("analyze shift roster and calendar_sync")
            self.assertEqual(task["selected_agent"], "shift")
            self.assertTrue(task["requires_confirmation"])
            self.assertEqual(task["status"], "awaiting_confirmation")

            confirmed = runtime.confirm(task["task_id"])
            self.assertTrue(confirmed["confirmed"])
            self.assertEqual(confirmed["status"], "completed")

    def test_shared_context_is_persisted_locally(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SharedContextStore(tmp)
            store.merge("shared:research", {"project": "Research OS"})
            reloaded = SharedContextStore(tmp)
            self.assertEqual(reloaded.get("shared:research")["project"], "Research OS")

    def test_runtime_dashboard_reports_active_components(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self._runtime(tmp)
            dashboard = runtime.dashboard()
            self.assertEqual(dashboard["event_bus"], "active")
            self.assertEqual(dashboard["task_queue"], "active")
            self.assertEqual(dashboard["shared_context"], "local_persistent")


if __name__ == "__main__":
    unittest.main()
