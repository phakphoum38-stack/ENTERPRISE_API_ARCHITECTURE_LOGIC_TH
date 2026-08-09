#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from v2_brain_core import ActivityLedger
from v2_execution_controller import CheckpointStore, ExecutionController, ExecutionRequest
from v2_tool_registry import ToolDefinition, ToolRegistry


class ExecutionControllerTests(unittest.TestCase):
    def make_controller(self, root: str, registry: ToolRegistry, *, max_attempts: int = 3) -> ExecutionController:
        return ExecutionController(
            tools=registry,
            ledger=ActivityLedger(root),
            checkpoints=CheckpointStore(root),
            max_attempts=max_attempts,
        )

    def test_missing_permission_blocks_adapter_before_invocation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            calls = {"count": 0}
            registry = ToolRegistry(())
            registry.register(
                ToolDefinition(
                    "test.read",
                    "1.0.0",
                    "Read",
                    "Read-only test tool.",
                    ("read",),
                    permissions=("runtime.read",),
                )
            )
            def adapter(action, payload, dry_run):
                calls["count"] += 1
                return {"ok": True}
            registry.register_adapter("test.read", adapter)
            controller = self.make_controller(tmp, registry)
            result = controller.execute(
                ExecutionRequest(session_id="s1", tool_id="test.read", action="get")
            )
            self.assertEqual("blocked", result.status)
            self.assertEqual(0, calls["count"])

    def test_mutating_tool_waits_for_explicit_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            calls = {"count": 0}
            registry = ToolRegistry(())
            registry.register(
                ToolDefinition(
                    "test.write",
                    "1.0.0",
                    "Write",
                    "Mutation test tool.",
                    ("write",),
                    permissions=("state.write",),
                    mutating=True,
                    idempotent=True,
                )
            )
            def adapter(action, payload, dry_run):
                calls["count"] += 1
                return {"written": payload.get("value")}
            registry.register_adapter("test.write", adapter)
            controller = self.make_controller(tmp, registry)
            request = ExecutionRequest(
                session_id="s2",
                tool_id="test.write",
                action="set",
                payload={"value": 7},
                granted_permissions=("state.write",),
                idempotency_key="write-7",
            )
            waiting = controller.execute(request)
            self.assertEqual("awaiting_approval", waiting.status)
            self.assertTrue(waiting.approval_required)
            self.assertEqual(0, calls["count"])

            completed = controller.resume(
                waiting.checkpoint_id,
                ExecutionRequest(
                    session_id="s2",
                    tool_id="test.write",
                    action="set",
                    payload={"value": 7},
                    granted_permissions=("state.write",),
                    approved=True,
                    idempotency_key="write-7",
                ),
            )
            self.assertEqual("completed", completed.status)
            self.assertEqual({"written": 7}, completed.output)
            self.assertEqual(1, calls["count"])

    def test_dry_run_of_mutating_tool_does_not_require_write_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = ToolRegistry(())
            registry.register(
                ToolDefinition(
                    "test.preview",
                    "1.0.0",
                    "Preview",
                    "Dry-run mutation preview.",
                    ("preview",),
                    permissions=("state.write",),
                    mutating=True,
                    supports_dry_run=True,
                )
            )
            registry.register_adapter(
                "test.preview",
                lambda action, payload, dry_run: {"dry_run": dry_run, "value": payload.get("value")},
            )
            controller = self.make_controller(tmp, registry)
            result = controller.execute(
                ExecutionRequest(
                    session_id="s3",
                    tool_id="test.preview",
                    action="set",
                    payload={"value": 1},
                    granted_permissions=("state.write",),
                    dry_run=True,
                )
            )
            self.assertEqual("completed", result.status)
            self.assertFalse(result.approval_required)
            self.assertTrue(result.output["dry_run"])

    def test_idempotent_tool_retries_with_bound_and_records_observations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            attempts = {"count": 0}
            registry = ToolRegistry(())
            registry.register(
                ToolDefinition(
                    "test.retry",
                    "1.0.0",
                    "Retry",
                    "Idempotent retry test.",
                    ("retry",),
                    permissions=("runtime.read",),
                    idempotent=True,
                )
            )
            def adapter(action, payload, dry_run):
                attempts["count"] += 1
                if attempts["count"] < 3:
                    raise RuntimeError("temporary failure")
                return {"ok": True}
            registry.register_adapter("test.retry", adapter)
            controller = self.make_controller(tmp, registry, max_attempts=3)
            result = controller.execute(
                ExecutionRequest(
                    session_id="s4",
                    tool_id="test.retry",
                    action="get",
                    granted_permissions=("runtime.read",),
                )
            )
            self.assertEqual("completed", result.status)
            self.assertEqual(3, result.attempts)
            self.assertEqual(["failed", "failed", "completed"], [item.status for item in result.observations])

    def test_non_idempotent_tool_never_auto_retries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            attempts = {"count": 0}
            registry = ToolRegistry(())
            registry.register(
                ToolDefinition(
                    "test.once",
                    "1.0.0",
                    "Once",
                    "Non-idempotent test.",
                    ("once",),
                    permissions=("runtime.read",),
                    idempotent=False,
                )
            )
            def adapter(action, payload, dry_run):
                attempts["count"] += 1
                raise RuntimeError("fail once")
            registry.register_adapter("test.once", adapter)
            controller = self.make_controller(tmp, registry)
            result = controller.execute(
                ExecutionRequest(
                    session_id="s5",
                    tool_id="test.once",
                    action="run",
                    granted_permissions=("runtime.read",),
                )
            )
            self.assertEqual("failed", result.status)
            self.assertEqual(1, result.attempts)
            self.assertEqual(1, attempts["count"])

    def test_idempotency_key_reuses_completed_result_without_second_adapter_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            calls = {"count": 0}
            registry = ToolRegistry(())
            registry.register(
                ToolDefinition(
                    "test.idempotent",
                    "1.0.0",
                    "Idempotent",
                    "Idempotency result reuse test.",
                    ("read",),
                    permissions=("runtime.read",),
                    idempotent=True,
                )
            )
            def adapter(action, payload, dry_run):
                calls["count"] += 1
                return {"call": calls["count"]}
            registry.register_adapter("test.idempotent", adapter)
            controller = self.make_controller(tmp, registry)
            request = ExecutionRequest(
                session_id="s6",
                tool_id="test.idempotent",
                action="get",
                granted_permissions=("runtime.read",),
                idempotency_key="same-request",
            )
            first = controller.execute(request)
            second = controller.execute(request)
            self.assertEqual("completed", first.status)
            self.assertTrue(second.reused)
            self.assertEqual(1, calls["count"])
            self.assertEqual(first.execution_id, second.execution_id)

    def test_checkpoint_restart_marks_running_execution_interrupted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = CheckpointStore(tmp)
            store.save(
                "checkpoint-running",
                {
                    "execution_id": "execution-running",
                    "session_id": "s7",
                    "tool_id": "test.read",
                    "action": "get",
                    "status": "running",
                },
            )
            restarted = CheckpointStore(tmp)
            state = restarted.get("checkpoint-running")
            self.assertEqual("interrupted", state["status"])
            self.assertTrue(state["recovery_required"])

    def test_checkpoint_and_ledger_redact_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = ToolRegistry(())
            registry.register(
                ToolDefinition(
                    "test.secret-safe",
                    "1.0.0",
                    "Secret Safe",
                    "Secret redaction test.",
                    ("read",),
                    permissions=("runtime.read",),
                )
            )
            registry.register_adapter(
                "test.secret-safe",
                lambda action, payload, dry_run: {"api_key": payload.get("api_key"), "ok": True},
            )
            controller = self.make_controller(tmp, registry)
            result = controller.execute(
                ExecutionRequest(
                    session_id="s8",
                    tool_id="test.secret-safe",
                    action="get",
                    payload={"api_key": "never-persist-me"},
                    granted_permissions=("runtime.read",),
                )
            )
            self.assertEqual("completed", result.status)
            checkpoint_text = (Path(tmp) / "intelligence" / "execution_checkpoints.json").read_text(encoding="utf-8")
            ledger_text = (Path(tmp) / "intelligence" / "activity_ledger.jsonl").read_text(encoding="utf-8")
            self.assertNotIn("never-persist-me", checkpoint_text)
            self.assertNotIn("never-persist-me", ledger_text)
            json.loads(checkpoint_text)


if __name__ == "__main__":
    unittest.main()
