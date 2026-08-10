#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest

from agent_platform import AgentRegistry
from v2_brain_core import ActivityLedger, ResearchOSBrain, WorkingMemory
from v2_execution_hardening import HardenedExecutionController, SecretAwareCheckpointStore
from v2_skill_executor import SKILL_EXECUTION_CONTRACT, SkillExecutionRequest, SkillExecutor
from v2_skill_registry import SkillDefinition, SkillRegistry
from v2_tool_registry import ToolDefinition, ToolRegistry


class SkillExecutorTests(unittest.TestCase):
    def make_stack(self, root: str, *, output: dict | None = None, mutating: bool = False):
        skills = SkillRegistry(
            (
                SkillDefinition(
                    "test.execute",
                    "1.0.0",
                    "Execute Test",
                    "Test skill that requires one execution capability.",
                    ("test_execute",),
                    required_tool_capabilities=("test_execute",),
                    permissions=("runtime.read",) if not mutating else ("runtime.read", "state.write"),
                    required_evidence=("result",),
                ),
            )
        )
        tools = ToolRegistry(())
        tools.register(
            ToolDefinition(
                "test.executor",
                "1.0.0",
                "Test Executor",
                "Executes a deterministic test adapter.",
                ("test_execute",),
                permissions=("runtime.read",) if not mutating else ("state.write",),
                mutating=mutating,
                idempotent=True,
            )
        )
        calls = {"count": 0}

        def adapter(action, payload, dry_run):
            calls["count"] += 1
            if output is not None:
                return dict(output)
            return {"result": "ok", "action": action, "dry_run": dry_run, "echo": dict(payload)}

        tools.register_adapter("test.executor", adapter)
        brain = ResearchOSBrain(
            registry=AgentRegistry(),
            working_memory=WorkingMemory(root),
            ledger=ActivityLedger(root),
        )
        execution = HardenedExecutionController(
            tools=tools,
            ledger=brain.ledger,
            checkpoints=SecretAwareCheckpointStore(root),
        )
        executor = SkillExecutor(skills=skills, tools=tools, execution=execution, brain=brain)
        return executor, calls

    def test_skill_resolves_tool_by_capability_and_verifies_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            executor, calls = self.make_stack(tmp)
            result = executor.execute(
                SkillExecutionRequest(
                    session_id="skill-ok",
                    skill_id="test.execute",
                    action="run",
                    granted_permissions=("runtime.read",),
                )
            )
            self.assertEqual(SKILL_EXECUTION_CONTRACT, result.contract)
            self.assertEqual("verified", result.status)
            self.assertEqual("test.executor", result.selected_tool_id)
            self.assertTrue(result.verification["verified"])
            self.assertEqual(1, calls["count"])

    def test_skill_permission_blocks_before_adapter_invocation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            executor, calls = self.make_stack(tmp)
            result = executor.execute(
                SkillExecutionRequest(
                    session_id="skill-blocked",
                    skill_id="test.execute",
                    action="run",
                )
            )
            self.assertEqual("blocked", result.status)
            self.assertTrue(any("skill permission missing" in item for item in result.blocked_reasons))
            self.assertEqual(0, calls["count"])

    def test_post_execution_verification_blocks_unsupported_completion_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            executor, calls = self.make_stack(tmp, output={"message": "ran without result evidence"})
            result = executor.execute(
                SkillExecutionRequest(
                    session_id="skill-no-evidence",
                    skill_id="test.execute",
                    action="run",
                    granted_permissions=("runtime.read",),
                )
            )
            self.assertEqual("verification_failed", result.status)
            self.assertFalse(result.verification["verified"])
            self.assertIn("evidence missing: result", result.blocked_reasons)
            self.assertEqual(1, calls["count"])

    def test_mutating_skill_requires_execution_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            executor, calls = self.make_stack(tmp, mutating=True)
            waiting = executor.execute(
                SkillExecutionRequest(
                    session_id="skill-write",
                    skill_id="test.execute",
                    action="write",
                    granted_permissions=("runtime.read", "state.write"),
                )
            )
            self.assertEqual("awaiting_approval", waiting.status)
            self.assertEqual(0, calls["count"])

            completed = executor.execute(
                SkillExecutionRequest(
                    session_id="skill-write-approved",
                    skill_id="test.execute",
                    action="write",
                    granted_permissions=("runtime.read", "state.write"),
                    approved=True,
                )
            )
            self.assertEqual("verified", completed.status)
            self.assertEqual(1, calls["count"])

    def test_reflected_secret_is_scrubbed_before_skill_result_and_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            secret = "skill-secret-123456789"
            executor, _ = self.make_stack(
                tmp,
                output={"result": "ok", "message": f"credential={secret}"},
            )
            result = executor.execute(
                SkillExecutionRequest(
                    session_id="skill-secret",
                    skill_id="test.execute",
                    action="run",
                    granted_permissions=("runtime.read",),
                    secret_values=(secret,),
                )
            )
            self.assertEqual("verified", result.status)
            self.assertNotIn(secret, repr(result))
            self.assertIn("[REDACTED]", repr(result))

    def test_missing_tool_capability_blocks_without_guessing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills = SkillRegistry(
                (
                    SkillDefinition(
                        "test.missing-tool",
                        "1.0.0",
                        "Missing Tool",
                        "Requires a capability that is not installed.",
                        ("missing_tool",),
                        required_tool_capabilities=("does_not_exist",),
                    ),
                )
            )
            tools = ToolRegistry(())
            brain = ResearchOSBrain(
                registry=AgentRegistry(),
                working_memory=WorkingMemory(tmp),
                ledger=ActivityLedger(tmp),
            )
            execution = HardenedExecutionController(
                tools=tools,
                ledger=brain.ledger,
                checkpoints=SecretAwareCheckpointStore(tmp),
            )
            executor = SkillExecutor(skills=skills, tools=tools, execution=execution, brain=brain)
            result = executor.execute(
                SkillExecutionRequest(
                    session_id="missing-tool",
                    skill_id="test.missing-tool",
                    action="run",
                )
            )
            self.assertEqual("blocked", result.status)
            self.assertTrue(any("required tool capability unavailable" in item for item in result.blocked_reasons))


if __name__ == "__main__":
    unittest.main()
