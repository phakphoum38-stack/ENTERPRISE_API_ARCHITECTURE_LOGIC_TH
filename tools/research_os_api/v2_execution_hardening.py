#!/usr/bin/env python3
"""Phase 4 secret-aware hardening for Brain tool execution.

The Phase 3 controller remains the stable execution state machine. This module
adds an ephemeral secret scope around it so reflected credentials in adapter
output, exceptions, observations, checkpoints and ledger events are scrubbed
without removing the real credential from the in-memory adapter request.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from v2_brain_core import ActivityLedger
from v2_brain_decision import DecisionEngine
from v2_execution_controller import (
    CheckpointStore,
    ExecutionController,
    ExecutionRequest,
    ExecutionResult,
)
from v2_secret_redactor import (
    discover_secret_values,
    redaction_status,
    sanitize_request_fields,
    secret_scope,
)
from v2_tool_registry import ToolRegistry


EXECUTION_HARDENING_CONTRACT = "brain-execution-hardening-phase-4"


@dataclass(frozen=True)
class SecretAwareExecutionRequest(ExecutionRequest):
    """Execution request with explicit ephemeral secrets that are never persisted."""

    secret_values: tuple[str, ...] = ()


class SecretAwareCheckpointStore(CheckpointStore):
    """Checkpoint store that scrubs active secret values from every write."""

    def save(self, checkpoint_id: str, values: Mapping[str, Any]) -> dict[str, Any]:
        safe = sanitize_request_fields(dict(values))
        return super().save(checkpoint_id, safe)


class SecretAwareLedger:
    """Sanitizing facade over the canonical Brain ActivityLedger."""

    def __init__(self, delegate: ActivityLedger) -> None:
        self.delegate = delegate

    def record(
        self,
        event_type: str,
        *,
        session_id: str,
        payload: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.delegate.record(
            event_type,
            session_id=session_id,
            payload=sanitize_request_fields(dict(payload or {})),
        )

    def list(self, *, session_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        return self.delegate.list(session_id=session_id, limit=limit)


class HardenedExecutionController(ExecutionController):
    """Phase 3 execution semantics plus Phase 4 secret-aware persistence."""

    def __init__(
        self,
        *,
        tools: ToolRegistry,
        decisions: DecisionEngine | None = None,
        ledger: ActivityLedger | None = None,
        checkpoints: SecretAwareCheckpointStore | None = None,
        max_attempts: int = 3,
    ) -> None:
        canonical_ledger = ledger or ActivityLedger()
        super().__init__(
            tools=tools,
            decisions=decisions,
            ledger=SecretAwareLedger(canonical_ledger),  # type: ignore[arg-type]
            checkpoints=checkpoints or SecretAwareCheckpointStore(),
            max_attempts=max_attempts,
        )
        self.canonical_ledger = canonical_ledger

    @staticmethod
    def _secrets(request: ExecutionRequest) -> tuple[str, ...]:
        explicit: Iterable[str] = getattr(request, "secret_values", ())
        return discover_secret_values(
            request.payload,
            request.evidence,
            explicit=explicit,
        )

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        with secret_scope(self._secrets(request)):
            return super().execute(request)

    def resume(self, checkpoint_id: str, request: ExecutionRequest) -> ExecutionResult:
        with secret_scope(self._secrets(request)):
            return super().resume(checkpoint_id, request)

    def dashboard(self) -> dict[str, Any]:
        report = super().dashboard()
        report.update(
            {
                "hardening_contract": EXECUTION_HARDENING_CONTRACT,
                "secret_redaction": redaction_status(),
                "secret_persistence": "ephemeral_value_aware_redacted_only",
            }
        )
        return report
