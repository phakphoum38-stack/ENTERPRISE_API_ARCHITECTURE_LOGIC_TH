import os
import tempfile
import unittest
from unittest.mock import patch

from agent_platform import AgentRegistry, AgentRouter
from agent_runtime import AgentEventBus, AgentTaskQueue, SharedContextStore


class AgentRuntimeTest(unittest.TestCase):
    def _runtime(self, tmp: str, router: AgentRouter | None = None) -> AgentTaskQueue:
        return AgentTaskQueue(
            router=router,
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

    def test_runtime_events_preserve_correlation_and_orchestration_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self._runtime(tmp)
            task = runtime.submit(
                "research runtime observability",
                requested_agent="research",
                context={
                    "orchestration_run_id": "run-observe-1",
                    "correlation_id": "corr-observe-1",
                },
            )
            self.assertEqual(task["run_id"], "run-observe-1")
            self.assertEqual(task["correlation_id"], "corr-observe-1")
            self.assertEqual(task["result"]["run_id"], "run-observe-1")
            events = runtime.events.list(task_id=task["task_id"])
            self.assertTrue(events)
            self.assertEqual({event["run_id"] for event in events}, {"run-observe-1"})
            self.assertEqual(
                {event["correlation_id"] for event in events},
                {"corr-observe-1"},
            )

    def test_developer_task_uses_developer_agent(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self._runtime(tmp, AgentRouter(AgentRegistry()))
            task = runtime.submit("debug code api build", confirmed=True)
            self.assertEqual(task["selected_agent"], "developer")
            self.assertEqual(task["status"], "completed")

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

    def test_runtime_attaches_adaptive_brain_plan_without_external_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self._runtime(tmp, AgentRouter(AgentRegistry()))
            task = runtime.submit(
                "research evidence with agent tools",
                context={
                    "brain_complexity_level": 6,
                    "brain_requested_workers": 46656,
                    "brain_budget_workers": 12,
                    "brain_ready_workers": 8,
                },
            )
            plan = task["result"]["brain_plan"]
            self.assertEqual(plan["hierarchy"]["max_leaf_capacity"], 6**6)
            self.assertEqual(plan["hierarchy"]["active_workers"], 8)
            self.assertTrue(plan["hierarchy"]["backpressure_applied"])
            self.assertFalse(plan["requires_external_api_key"])

    def test_runtime_auto_selects_six_cubed_assistant_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self._runtime(tmp, AgentRouter(AgentRegistry()))
            task = runtime.submit("ขอผู้ช่วย 6^3 จัดทีมเขียนระบบ")
            plan = task["result"]["brain_plan"]
            self.assertEqual(plan["assistant_profile"]["mode"], "assistant_6x3")
            self.assertEqual(plan["hierarchy"]["complexity_level"], 3)
            self.assertEqual(plan["hierarchy"]["requested_workers"], 6**3)
            self.assertEqual(plan["cognition"]["mode"], "assistant_6x3")

    def test_runtime_dashboard_reports_active_components(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self._runtime(tmp, AgentRouter(AgentRegistry()))
            dashboard = runtime.dashboard()
            self.assertEqual(dashboard["runtime"], "agent_runtime_2.0")
            self.assertEqual(dashboard["event_bus"], "active")
            self.assertEqual(dashboard["task_queue"], "active")
            self.assertEqual(dashboard["shared_context"], "local_persistent")
            self.assertTrue(dashboard["agent_readiness"]["ready"])
            self.assertEqual(dashboard["agent_readiness"]["ready_count"], 6)
            self.assertEqual(dashboard["brain"]["capacity"]["max_leaf_capacity"], 6**6)
            self.assertEqual(dashboard["brain"]["skills"]["skill_count"], 10)


if __name__ == "__main__":
    unittest.main()
