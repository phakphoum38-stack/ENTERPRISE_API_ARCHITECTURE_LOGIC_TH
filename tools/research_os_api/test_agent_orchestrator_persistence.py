from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_orchestrator import AgentOrchestrator
from agent_runtime import AgentTaskQueue, SharedContextStore


class DurableOrchestrationTests(unittest.TestCase):
    def _orchestrator(self, root: Path) -> AgentOrchestrator:
        runtime = AgentTaskQueue(context_store=SharedContextStore(root))
        return AgentOrchestrator(
            runtime=runtime,
            storage_path=root / "agents" / "orchestrations.json",
        )

    def test_run_survives_runtime_restart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = self._orchestrator(root)
            created = first.create_run(
                "research durable orchestration",
                [
                    {
                        "step_id": "research",
                        "objective": "research architecture",
                        "requested_agent": "research",
                    }
                ],
            )

            restarted = self._orchestrator(root)
            restored = restarted.get(created["run_id"])

            self.assertEqual(restored["run_id"], created["run_id"])
            self.assertEqual(restored["objective"], "research durable orchestration")
            self.assertEqual(restored["status"], "planned")
            self.assertEqual(len(restarted.list()), 1)
            self.assertEqual(restored["events"][0]["event_type"], "run.created")

            payload = json.loads(
                (root / "agents" / "orchestrations.json").read_text(encoding="utf-8")
            )
            self.assertEqual(payload["schema_version"], 1)

    def test_audit_timeline_survives_restart_and_history_is_filterable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = self._orchestrator(root)
            created = first.create_run(
                "research audit history",
                [
                    {
                        "step_id": "research",
                        "objective": "inspect durable audit state",
                        "requested_agent": "research",
                    }
                ],
            )
            completed = first.execute(created["run_id"])
            self.assertEqual(completed["status"], "completed")

            restarted = self._orchestrator(root)
            filtered = restarted.list(
                status="completed",
                query="audit",
                agent="research",
                limit=10,
            )
            self.assertEqual(len(filtered), 1)
            self.assertEqual(filtered[0]["run_id"], created["run_id"])

            timeline = restarted.timeline(created["run_id"])
            event_types = [event["event_type"] for event in timeline]
            self.assertIn("run.created", event_types)
            self.assertIn("run.execution_started", event_types)
            self.assertIn("step.completed", event_types)
            self.assertIn("run.status_changed", event_types)

    def test_interrupted_run_is_recovered_and_can_resume(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = self._orchestrator(root)
            created = first.create_run(
                "resume after restart",
                [
                    {
                        "step_id": "research",
                        "objective": "research repository state",
                        "requested_agent": "research",
                    }
                ],
            )
            state_path = root / "agents" / "orchestrations.json"
            payload = json.loads(state_path.read_text(encoding="utf-8"))
            payload["runs"][0]["status"] = "running"
            payload["runs"][0]["steps"][0]["status"] = "running"
            state_path.write_text(json.dumps(payload), encoding="utf-8")

            restarted = self._orchestrator(root)
            restored = restarted.get(created["run_id"])
            self.assertEqual(restored["status"], "interrupted")
            self.assertEqual(restored["steps"][0]["status"], "interrupted")
            self.assertIn(
                "run.recovered_after_restart",
                [event["event_type"] for event in restarted.timeline(created["run_id"])],
            )

            resumed = restarted.execute(created["run_id"])
            self.assertEqual(resumed["status"], "completed")
            self.assertEqual(resumed["steps"][0]["status"], "completed")

    def test_confirmation_can_resume_after_restart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = self._orchestrator(root)
            created = first.create_run(
                "sync shift calendar",
                [
                    {
                        "step_id": "shift",
                        "objective": "analyze shift roster and calendar_sync",
                        "requested_agent": "shift",
                    }
                ],
            )
            waiting = first.execute(created["run_id"])
            self.assertEqual(waiting["status"], "awaiting_confirmation")

            restarted = self._orchestrator(root)
            restored = restarted.get(created["run_id"])
            self.assertEqual(restored["status"], "awaiting_confirmation")

            confirmed = restarted.confirm(created["run_id"])
            self.assertEqual(confirmed["status"], "completed")
            self.assertEqual(confirmed["steps"][0]["status"], "completed")


if __name__ == "__main__":
    unittest.main()
