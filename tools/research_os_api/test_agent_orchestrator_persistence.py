from __future__ import annotations

import json
import tempfile
import unittest
import uuid
from pathlib import Path

from agent_orchestrator import AgentOrchestrator
from agent_platform import AgentRouter
from agent_runtime import AgentTaskQueue, SharedContextStore


class ControlledRuntime:
    def __init__(self, failures_before_success: int) -> None:
        self.router = AgentRouter()
        self.failures_before_success = failures_before_success
        self.calls = 0

    def submit(self, objective, requested_agent=None, context=None, confirmed=False):
        self.calls += 1
        failed = self.calls <= self.failures_before_success
        return {
            "task_id": str(uuid.uuid4()),
            "status": "failed" if failed else "completed",
            "result": None if failed else {"objective": objective, "context": dict(context or {})},
            "error": "transient test failure" if failed else None,
        }


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
            self.assertEqual(payload["schema_version"], 2)

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

    def test_bounded_retry_succeeds_before_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = ControlledRuntime(failures_before_success=1)
            orchestrator = AgentOrchestrator(
                runtime=runtime,
                storage_path=root / "agents" / "orchestrations.json",
            )
            created = orchestrator.create_run(
                "retry transient failure",
                [{"step_id": "research", "objective": "retry me", "max_attempts": 2}],
            )

            first = orchestrator.execute(created["run_id"])
            self.assertEqual(first["status"], "failed")
            self.assertEqual(first["steps"][0]["attempt_count"], 1)

            retried = orchestrator.retry(created["run_id"], "research")
            self.assertEqual(retried["status"], "completed")
            self.assertEqual(retried["steps"][0]["attempt_count"], 2)
            event_types = [event["event_type"] for event in orchestrator.timeline(created["run_id"])]
            self.assertIn("step.retry_requested", event_types)

    def test_retry_limit_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = ControlledRuntime(failures_before_success=10)
            orchestrator = AgentOrchestrator(
                runtime=runtime,
                storage_path=root / "agents" / "orchestrations.json",
            )
            created = orchestrator.create_run(
                "bounded retry failure",
                [{"step_id": "research", "objective": "always fail", "max_attempts": 2}],
            )
            orchestrator.execute(created["run_id"])
            second = orchestrator.retry(created["run_id"], "research")
            self.assertEqual(second["status"], "failed")
            self.assertEqual(second["steps"][0]["attempt_count"], 2)
            with self.assertRaisesRegex(ValueError, "no retryable failed steps"):
                orchestrator.retry(created["run_id"], "research")

    def test_cancel_is_persistent_and_blocks_execution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = self._orchestrator(root)
            created = first.create_run(
                "cancel durable run",
                [{"step_id": "research", "objective": "do not execute"}],
            )
            cancelled = first.cancel(created["run_id"])
            self.assertEqual(cancelled["status"], "cancelled")
            self.assertEqual(cancelled["steps"][0]["status"], "cancelled")

            restarted = self._orchestrator(root)
            restored = restarted.get(created["run_id"])
            self.assertEqual(restored["status"], "cancelled")
            with self.assertRaisesRegex(ValueError, "orchestration run is cancelled"):
                restarted.execute(created["run_id"])
            self.assertIn(
                "run.cancelled",
                [event["event_type"] for event in restarted.timeline(created["run_id"])],
            )

    def test_schema_v1_state_migrates_without_data_loss(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_path = root / "agents" / "orchestrations.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "updated_at": 1.0,
                        "runs": [
                            {
                                "run_id": "legacy-run",
                                "objective": "preserve v1 durable state",
                                "status": "completed",
                                "created_at": 1.0,
                                "updated_at": 2.0,
                                "steps": [
                                    {
                                        "step_id": "research",
                                        "objective": "legacy research step",
                                        "requested_agent": "research",
                                        "depends_on": [],
                                        "context": {"legacy": True},
                                        "status": "completed",
                                        "task_id": "legacy-task",
                                        "result": {"ok": True},
                                        "error": None,
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            orchestrator = AgentOrchestrator(storage_path=state_path)
            migrated = orchestrator.get("legacy-run")
            self.assertEqual(migrated["run_id"], "legacy-run")
            self.assertEqual(migrated["status"], "completed")
            self.assertEqual(migrated["steps"][0]["result"], {"ok": True})
            self.assertEqual(migrated["steps"][0]["attempt_count"], 0)
            self.assertEqual(migrated["steps"][0]["max_attempts"], 3)

            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["schema_version"], 2)
            self.assertEqual(persisted["runs"][0]["run_id"], "legacy-run")
            self.assertEqual(persisted["runs"][0]["steps"][0]["step_id"], "research")

    def test_openapi_preserves_v1_routes_and_declares_phase1_extensions(self) -> None:
        contract = Path(__file__).with_name("openapi.yaml").read_text(encoding="utf-8")
        required_paths = [
            "/v1/agents/orchestrations:",
            "/v1/agents/orchestrations/{run_id}:",
            "/v1/agents/orchestrations/{run_id}/execute:",
            "/v1/agents/orchestrations/{run_id}/confirm:",
            "/v1/agents/orchestrations/{run_id}/timeline:",
            "/v1/agents/orchestrations/{run_id}/retry:",
            "/v1/agents/orchestrations/{run_id}/cancel:",
        ]
        for path in required_paths:
            self.assertIn(path, contract)
        self.assertIn("max_attempts:", contract)
        self.assertIn("maximum: 5", contract)
        self.assertIn("maximum: 200", contract)


if __name__ == "__main__":
    unittest.main()
