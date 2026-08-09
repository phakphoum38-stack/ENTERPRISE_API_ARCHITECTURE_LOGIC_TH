from __future__ import annotations

import tempfile
import unittest

from agent_orchestrator import AgentOrchestrator
from agent_platform import AgentRouter
from agent_runtime import AgentEventBus, AgentTaskQueue, SharedContextStore


class AgentOrchestratorTests(unittest.TestCase):
    def _orchestrator(self) -> AgentOrchestrator:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        runtime = AgentTaskQueue(
            event_bus=AgentEventBus(),
            context_store=SharedContextStore(self.temp.name),
        )
        return AgentOrchestrator(runtime=runtime)

    def test_dependency_chain_passes_previous_result_to_next_step(self) -> None:
        orchestrator = self._orchestrator()
        run = orchestrator.create_run(
            "Research a repository and review its workflow",
            [
                {
                    "step_id": "research",
                    "objective": "research architecture evidence",
                    "requested_agent": "research",
                },
                {
                    "step_id": "github",
                    "objective": "review github repository workflow",
                    "requested_agent": "github",
                    "depends_on": ["research"],
                },
            ],
        )

        result = orchestrator.execute(run["run_id"])

        self.assertEqual(result["status"], "completed")
        self.assertEqual([step["status"] for step in result["steps"]], ["completed", "completed"])
        dependency_results = result["steps"][1]["result"]["context"]["dependency_results"]
        self.assertIn("research", dependency_results)
        self.assertEqual(dependency_results["research"]["agent_id"], "research")

    def test_write_capable_step_waits_for_confirmation_then_completes(self) -> None:
        orchestrator = self._orchestrator()
        run = orchestrator.create_run(
            "Analyze roster and prepare calendar synchronization",
            [
                {
                    "step_id": "shift-write",
                    "objective": "analyze shift roster and calendar_sync",
                    "requested_agent": "shift",
                }
            ],
        )

        waiting = orchestrator.execute(run["run_id"])
        self.assertEqual(waiting["status"], "awaiting_confirmation")
        self.assertEqual(waiting["steps"][0]["status"], "awaiting_confirmation")

        confirmed = orchestrator.confirm(run["run_id"])
        self.assertEqual(confirmed["status"], "completed")
        self.assertEqual(confirmed["steps"][0]["status"], "completed")

    def test_failed_dependency_prevents_dependent_execution(self) -> None:
        class FailingRuntime:
            def __init__(self) -> None:
                self.router = AgentRouter()
                self.calls: list[str] = []

            def submit(self, objective, requested_agent=None, context=None, confirmed=False):
                self.calls.append(objective)
                if objective == "fail first":
                    return {
                        "task_id": "failed-task",
                        "status": "failed",
                        "result": None,
                        "error": "simulated failure",
                    }
                return {
                    "task_id": "unexpected-task",
                    "status": "completed",
                    "result": {"agent_id": requested_agent},
                    "error": None,
                }

            def confirm(self, task_id):
                raise AssertionError("confirm should not be called")

        runtime = FailingRuntime()
        orchestrator = AgentOrchestrator(runtime=runtime, router=runtime.router)
        run = orchestrator.create_run(
            "Failure propagation",
            [
                {
                    "step_id": "first",
                    "objective": "fail first",
                    "requested_agent": "research",
                },
                {
                    "step_id": "second",
                    "objective": "must not execute",
                    "requested_agent": "github",
                    "depends_on": ["first"],
                },
            ],
        )

        result = orchestrator.execute(run["run_id"])

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["steps"][0]["error"], "simulated failure")
        self.assertEqual(result["steps"][1]["error"], "dependency failed or cancelled")
        self.assertEqual(runtime.calls, ["fail first"])

    def test_rejects_duplicate_and_missing_dependencies(self) -> None:
        orchestrator = self._orchestrator()
        with self.assertRaises(ValueError):
            orchestrator.create_run(
                "duplicate",
                [
                    {"step_id": "same", "objective": "one"},
                    {"step_id": "same", "objective": "two"},
                ],
            )
        with self.assertRaises(ValueError):
            orchestrator.create_run(
                "missing dependency",
                [
                    {
                        "step_id": "one",
                        "objective": "one",
                        "depends_on": ["does-not-exist"],
                    }
                ],
            )


if __name__ == "__main__":
    unittest.main()
