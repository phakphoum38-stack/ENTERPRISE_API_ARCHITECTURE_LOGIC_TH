#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from v2_brain_core import ActivityLedger
from v2_execution_hardening import (
    EXECUTION_HARDENING_CONTRACT,
    HardenedExecutionController,
    SecretAwareCheckpointStore,
    SecretAwareExecutionRequest,
)
from v2_tool_registry import ToolDefinition, ToolRegistry


class ExecutionHardeningTests(unittest.TestCase):
    def make_controller(self, root: str, registry: ToolRegistry) -> HardenedExecutionController:
        return HardenedExecutionController(
            tools=registry,
            ledger=ActivityLedger(root),
            checkpoints=SecretAwareCheckpointStore(root),
        )

    def test_reflected_secret_in_output_is_redacted_from_result_checkpoint_and_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            secret = "reflected-secret-123456789"
            registry = ToolRegistry(())
            registry.register(
                ToolDefinition(
                    "test.reflect",
                    "1.0.0",
                    "Reflect",
                    "Reflects an input for hardening validation.",
                    ("reflect",),
                    permissions=("runtime.read",),
                )
            )
            registry.register_adapter(
                "test.reflect",
                lambda action, payload, dry_run: {"message": f"adapter says {payload['credential']}"},
            )
            controller = self.make_controller(tmp, registry)
            result = controller.execute(
                SecretAwareExecutionRequest(
                    session_id="reflect-output",
                    tool_id="test.reflect",
                    action="run",
                    payload={"credential": secret},
                    secret_values=(secret,),
                    granted_permissions=("runtime.read",),
                )
            )
            self.assertEqual("completed", result.status)
            self.assertNotIn(secret, repr(result))
            self.assertIn("[REDACTED]", result.output["message"])
            checkpoint_text = (Path(tmp) / "intelligence" / "execution_checkpoints.json").read_text(encoding="utf-8")
            ledger_text = (Path(tmp) / "intelligence" / "activity_ledger.jsonl").read_text(encoding="utf-8")
            self.assertNotIn(secret, checkpoint_text)
            self.assertNotIn(secret, ledger_text)

    def test_secret_in_sensitive_input_field_is_discovered_without_explicit_secret_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            secret = "auto-discovered-secret-987654321"
            registry = ToolRegistry(())
            registry.register(
                ToolDefinition(
                    "test.auto-secret",
                    "1.0.0",
                    "Auto Secret",
                    "Returns a sensitive input under a neutral key.",
                    ("secret",),
                    permissions=("runtime.read",),
                )
            )
            registry.register_adapter(
                "test.auto-secret",
                lambda action, payload, dry_run: {"message": payload["api_key"]},
            )
            controller = self.make_controller(tmp, registry)
            result = controller.execute(
                SecretAwareExecutionRequest(
                    session_id="auto-secret",
                    tool_id="test.auto-secret",
                    action="run",
                    payload={"api_key": secret},
                    granted_permissions=("runtime.read",),
                )
            )
            self.assertEqual("completed", result.status)
            self.assertEqual("[REDACTED]", result.output["message"])
            self.assertNotIn(secret, repr(result))

    def test_adapter_exception_message_is_secret_scrubbed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            secret = "exception-secret-123456789"
            registry = ToolRegistry(())
            registry.register(
                ToolDefinition(
                    "test.secret-error",
                    "1.0.0",
                    "Secret Error",
                    "Raises an exception containing a secret.",
                    ("secret_error",),
                    permissions=("runtime.read",),
                    idempotent=False,
                )
            )

            def adapter(action, payload, dry_run):
                raise RuntimeError(f"provider rejected token {payload['token']}")

            registry.register_adapter("test.secret-error", adapter)
            controller = self.make_controller(tmp, registry)
            result = controller.execute(
                SecretAwareExecutionRequest(
                    session_id="secret-error",
                    tool_id="test.secret-error",
                    action="run",
                    payload={"token": secret},
                    granted_permissions=("runtime.read",),
                )
            )
            self.assertEqual("failed", result.status)
            self.assertNotIn(secret, result.error or "")
            self.assertIn("[REDACTED]", result.error or "")
            self.assertNotIn(secret, repr(result.observations))

    def test_dashboard_reports_phase_four_hardening_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            controller = self.make_controller(tmp, ToolRegistry(()))
            report = controller.dashboard()
            self.assertEqual(EXECUTION_HARDENING_CONTRACT, report["hardening_contract"])
            self.assertTrue(report["secret_redaction"]["value_aware"])
            self.assertFalse(report["secret_redaction"]["secret_values_persisted"])


if __name__ == "__main__":
    unittest.main()
