#!/usr/bin/env python3
from __future__ import annotations

# This suite intentionally lives in the consolidated Agent Platform gate so the
# final Phase 8 code/documentation SHA is validated without adding a workflow.
import tempfile
import unittest
from pathlib import Path

from agent_orchestrator import AgentOrchestrator
from agent_platform import AgentRegistry, AgentRouter
from agent_runtime import AgentEventBus, AgentTaskQueue, SharedContextStore
from v2_brain_core import ActivityLedger, ResearchOSBrain, WorkingMemory
from v2_brain_decision import DecisionEngine
from v2_execution_hardening import HardenedExecutionController, SecretAwareCheckpointStore
from v2_governed_task_runner import GovernedTaskRunner, GovernedTaskStore
from v2_skill_executor import SkillExecutor
from v2_skill_registry import SkillDefinition, SkillRegistry
from v2_tool_registry import ToolDefinition, ToolRegistry


class GovernedTaskRunnerTests(unittest.TestCase):
    def make_runner(self, root: str, *, mutating: bool = False):
        registry = AgentRegistry()
        memory = WorkingMemory(root)
        ledger = ActivityLedger(root)
        brain = ResearchOSBrain(registry=registry, working_memory=memory, ledger=ledger)
        permission = "runtime.write" if mutating else "runtime.read"
        skill = SkillDefinition(
            "test.research-work",
            "1.0.0",
            "Test Research Work",
            "Test-only governed task skill.",
            ("research",),
            required_tools=("test.research-tool",),
            permissions=(permission,),
            required_evidence=("value",),
        )
        skills = SkillRegistry((skill,))
        tool = ToolDefinition(
            "test.research-tool",
            "1.0.0",
            "Test Research Tool",
            "Test-only read or mutation adapter.",
            ("test_research",),
            permissions=(permission,),
            mutating=mutating,
            idempotent=True,
        )
        tools = ToolRegistry((tool,))
        calls: list[tuple[str, dict, bool]] = []

        def adapter(action: str, payload: dict, dry_run: bool):
            calls.append((action, dict(payload), dry_run))
            return {"value": payload.get("value") or "ok", "action": action}

        tools.register_adapter("test.research-tool", adapter)
        execution = HardenedExecutionController(
            tools=tools,
            decisions=DecisionEngine(),
            ledger=ledger,
            checkpoints=SecretAwareCheckpointStore(root),
        )
        skill_execution = SkillExecutor(
            skills=skills,
            tools=tools,
            execution=execution,
            brain=brain,
        )
        runtime = AgentTaskQueue(
            router=AgentRouter(registry),
            event_bus=AgentEventBus(),
            context_store=SharedContextStore(root),
        )
        orchestrator = AgentOrchestrator(
            runtime=runtime,
            storage_path=Path(root) / "agents" / "orchestrations.json",
        )
        runner = GovernedTaskRunner(
            brain=brain,
            skills=skills,
            skill_execution=skill_execution,
            orchestrator=orchestrator,
            store=GovernedTaskStore(root),
            ledger=ledger,
        )
        return runner, calls

    @staticmethod
    def binding(permission: str) -> dict:
        return {
            "capability": "research",
            "skill_id": "test.research-work",
            "action": "run",
            "payload": {"value": "evidence"},
            "granted_permissions": [permission],
        }

    def test_read_only_task_runs_goal_to_verified_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runner, calls = self.make_runner(tmp)
            prepared = runner.prepare(
                "evaluate evidence",
                session_id="phase8-read",
                bindings=[self.binding("runtime.read")],
            )
            self.assertEqual("prepared", prepared["status"])
            self.assertIsNotNone(prepared["orchestration_run_id"])

            completed = runner.start(prepared["task_id"])
            self.assertEqual("verified", completed["status"])
            self.assertTrue(completed["final_verification"]["verified"])
            self.assertEqual(1, completed["verified_step_count"])
            self.assertEqual("completed", completed["orchestration"]["status"])
            self.assertEqual(1, len(calls))
            self.assertEqual("run", calls[0][0])

    def test_mutation_waits_for_exact_pending_step_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runner, calls = self.make_runner(tmp, mutating=True)
            prepared = runner.prepare(
                "evaluate evidence",
                session_id="phase8-write",
                bindings=[self.binding("runtime.write")],
            )
            waiting = runner.start(prepared["task_id"])
            self.assertEqual("awaiting_approval", waiting["status"])
            self.assertEqual("task-1-research", waiting["pending_step_id"])
            self.assertEqual([], calls)

            completed = runner.approve_step(
                prepared["task_id"],
                "task-1-research",
            )
            self.assertEqual("verified", completed["status"])
            self.assertEqual(1, len(calls))

    def test_missing_capability_binding_fails_closed_before_orchestration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runner, calls = self.make_runner(tmp)
            blocked = runner.prepare(
                "evaluate evidence",
                session_id="phase8-blocked",
                bindings=[],
            )
            self.assertEqual("blocked", blocked["status"])
            self.assertIsNone(blocked["orchestration_run_id"])
            self.assertIn("missing skill/action binding for capability: research", blocked["blocked_reasons"])
            self.assertEqual([], calls)

    def test_raw_secret_material_never_enters_durable_task_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runner, _ = self.make_runner(tmp)
            with self.assertRaisesRegex(ValueError, "credential-like material"):
                runner.prepare(
                    "use sk-abcdefghijklmnopqrst for evidence",
                    session_id="phase8-secret-objective",
                    bindings=[self.binding("runtime.read")],
                )

            binding = self.binding("runtime.read")
            binding["payload"] = {"api_key": "must-never-persist"}
            with self.assertRaisesRegex(ValueError, "raw secret material"):
                runner.prepare(
                    "evaluate evidence",
                    session_id="phase8-secret-binding",
                    bindings=[binding],
                )
            self.assertFalse((Path(tmp) / "intelligence" / "governed_tasks.json").exists())

    def test_prepared_task_recovers_from_durable_orchestrator_and_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runner, _ = self.make_runner(tmp)
            prepared = runner.prepare(
                "evaluate evidence",
                session_id="phase8-restart",
                bindings=[self.binding("runtime.read")],
            )

            restarted, calls = self.make_runner(tmp)
            recovered = restarted.start(prepared["task_id"])
            self.assertEqual("verified", recovered["status"])
            self.assertEqual(1, len(calls))
            timeline = restarted.timeline(prepared["task_id"])
            self.assertTrue(timeline["orchestration"])
            self.assertTrue(timeline["brain_activity"])

    def test_dashboard_declares_no_unrestricted_shell_or_second_dag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runner, _ = self.make_runner(tmp)
            report = runner.dashboard()
            self.assertEqual("AgentOrchestrator", report["canonical_dependency_graph"])
            self.assertEqual("HardenedExecutionController only", report["tool_execution"])
            self.assertFalse(report["unrestricted_shell"])
            self.assertFalse(report["raw_secret_persistence"])


if __name__ == "__main__":
    unittest.main()
