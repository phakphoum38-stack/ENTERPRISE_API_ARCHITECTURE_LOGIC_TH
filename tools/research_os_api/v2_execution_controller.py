#!/usr/bin/env python3
"""Research OS AI Brain permissioned execution controller.

The controller is the only Brain Core path allowed to invoke registered tool
adapters. It enforces deterministic risk policy, permissions, evidence,
approval, dry-run semantics, bounded retry, idempotency reuse, observation
logging and durable checkpoints. Secret-bearing payloads are never persisted in
clear text.
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from v2_brain_core import ActivityLedger, redact_sensitive
from v2_brain_decision import ActionCandidate, DecisionEngine
from v2_tool_registry import ToolDefinition, ToolRegistry


@dataclass(frozen=True)
class ExecutionRequest:
    session_id: str
    tool_id: str
    action: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    granted_permissions: tuple[str, ...] = ()
    evidence: Mapping[str, Any] = field(default_factory=dict)
    approved: bool = False
    dry_run: bool = False
    idempotency_key: str | None = None
    correlation_id: str | None = None


@dataclass(frozen=True)
class ExecutionObservation:
    execution_id: str
    attempt: int
    status: str
    timestamp: float
    output: Mapping[str, Any] | None = None
    error_type: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class ExecutionResult:
    execution_id: str
    checkpoint_id: str
    session_id: str
    tool_id: str
    action: str
    status: str
    attempts: int
    approval_required: bool
    dry_run: bool
    reused: bool
    decision: Mapping[str, Any]
    output: Mapping[str, Any] | None = None
    error_type: str | None = None
    error: str | None = None
    observations: tuple[ExecutionObservation, ...] = ()


def _default_data_dir() -> Path:
    configured = os.getenv("RESEARCH_OS_DATA_DIR", "").strip()
    if configured:
        return Path(configured)
    if os.name == "nt":
        return Path(os.getenv("PROGRAMDATA", r"C:\ProgramData")) / "ResearchOS"
    return Path.home() / "ResearchOSData"


class CheckpointStore:
    """Durable local execution checkpoints with atomic writes."""

    def __init__(self, data_dir: str | os.PathLike[str] | None = None) -> None:
        root = Path(data_dir) if data_dir is not None else _default_data_dir()
        self.root = root / "intelligence"
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "execution_checkpoints.json"
        self._lock = threading.RLock()
        self.recover_interrupted()

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": 1, "checkpoints": {}}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return {"version": 1, "checkpoints": {}}
        if not isinstance(payload, dict):
            return {"version": 1, "checkpoints": {}}
        checkpoints = payload.get("checkpoints")
        if not isinstance(checkpoints, dict):
            checkpoints = {}
        return {"version": 1, "checkpoints": checkpoints}

    def _write(self, payload: Mapping[str, Any]) -> None:
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temp, self.path)

    def save(self, checkpoint_id: str, values: Mapping[str, Any]) -> dict[str, Any]:
        safe = redact_sensitive(dict(values))
        with self._lock:
            payload = self._read()
            checkpoints = payload["checkpoints"]
            current = checkpoints.get(checkpoint_id, {})
            if not isinstance(current, dict):
                current = {}
            current.update(safe)
            current["checkpoint_id"] = checkpoint_id
            current["updated_at"] = time.time()
            checkpoints[checkpoint_id] = current
            self._write(payload)
            return dict(current)

    def get(self, checkpoint_id: str) -> dict[str, Any]:
        with self._lock:
            value = self._read()["checkpoints"].get(checkpoint_id)
            if not isinstance(value, dict):
                raise ValueError(f"unknown checkpoint: {checkpoint_id}")
            return dict(value)

    def list(self, *, session_id: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            values = list(self._read()["checkpoints"].values())
        items = [dict(item) for item in values if isinstance(item, dict)]
        if session_id:
            items = [item for item in items if item.get("session_id") == session_id]
        return sorted(items, key=lambda item: float(item.get("updated_at", 0.0)), reverse=True)

    def find_completed(self, idempotency_key: str) -> dict[str, Any] | None:
        if not idempotency_key:
            return None
        for item in self.list():
            if (
                item.get("idempotency_key") == idempotency_key
                and item.get("status") == "completed"
            ):
                return item
        return None

    def recover_interrupted(self) -> int:
        with self._lock:
            payload = self._read()
            checkpoints = payload["checkpoints"]
            changed = 0
            for checkpoint in checkpoints.values():
                if isinstance(checkpoint, dict) and checkpoint.get("status") == "running":
                    checkpoint["status"] = "interrupted"
                    checkpoint["recovery_required"] = True
                    checkpoint["updated_at"] = time.time()
                    changed += 1
            if changed:
                self._write(payload)
            return changed


class ExecutionController:
    """Permission, approval, observation and recovery gate for tool adapters."""

    def __init__(
        self,
        *,
        tools: ToolRegistry,
        decisions: DecisionEngine | None = None,
        ledger: ActivityLedger | None = None,
        checkpoints: CheckpointStore | None = None,
        max_attempts: int = 3,
    ) -> None:
        if max_attempts < 1 or max_attempts > 5:
            raise ValueError("max_attempts must be between 1 and 5")
        self.tools = tools
        self.decisions = decisions or DecisionEngine()
        self.ledger = ledger or ActivityLedger()
        self.checkpoints = checkpoints or CheckpointStore()
        self.max_attempts = max_attempts
        self._lock = threading.RLock()

    @staticmethod
    def _candidate(tool: ToolDefinition, request: ExecutionRequest) -> ActionCandidate:
        effective_state_change = bool(tool.mutating and not request.dry_run)
        return ActionCandidate(
            action_id=f"{tool.tool_id}:{request.action}",
            description=f"Invoke {tool.tool_id} action {request.action}",
            state_change=effective_state_change,
            destructive=bool(tool.destructive and not request.dry_run),
            network=tool.network,
            secret_access=tool.secret_access,
            required_permissions=tool.permissions,
            required_evidence=(),
            utility=1,
        )

    def _decision(self, tool: ToolDefinition, request: ExecutionRequest) -> dict[str, Any]:
        summary = self.decisions.choose(
            [self._candidate(tool, request)],
            granted_permissions=request.granted_permissions,
            evidence=request.evidence,
        )
        payload = asdict(summary)
        # Research OS write policy is stricter than generic risk scoring: any real
        # mutation requires explicit approval, even when its numeric risk is low.
        if tool.mutating and not request.dry_run and summary.selected_action_id:
            payload["decision"] = "approval_required"
            if payload.get("risk"):
                payload["risk"]["approval_required"] = True
        return payload

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        if not request.session_id.strip():
            raise ValueError("session_id is required")
        if not request.action.strip():
            raise ValueError("tool action is required")
        tool = self.tools.get(request.tool_id)
        if not tool.enabled:
            raise ValueError(f"tool disabled: {request.tool_id}")
        if request.dry_run and not tool.supports_dry_run:
            raise ValueError(f"tool does not support dry-run: {request.tool_id}")

        if request.idempotency_key:
            completed = self.checkpoints.find_completed(request.idempotency_key)
            if completed is not None:
                if completed.get("tool_id") != request.tool_id or completed.get("action") != request.action:
                    raise ValueError("idempotency key already belongs to a different tool action")
                return self._result_from_checkpoint(completed, reused=True)

        execution_id = str(uuid.uuid4())
        checkpoint_id = execution_id
        decision = self._decision(tool, request)
        approval_required = decision.get("decision") == "approval_required"
        status = "planned"
        blocked_reason: str | None = None

        if decision.get("decision") == "blocked":
            status = "blocked"
            blocked_reason = str(decision.get("reason") or "action blocked")
        elif approval_required and not request.approved:
            status = "awaiting_approval"

        checkpoint = self.checkpoints.save(
            checkpoint_id,
            {
                "execution_id": execution_id,
                "session_id": request.session_id,
                "tool_id": request.tool_id,
                "action": request.action,
                "status": status,
                "attempts": 0,
                "approval_required": approval_required,
                "dry_run": request.dry_run,
                "idempotency_key": request.idempotency_key,
                "correlation_id": request.correlation_id or execution_id,
                "decision": decision,
                "safe_payload": redact_sensitive(dict(request.payload)),
                "safe_evidence": redact_sensitive(dict(request.evidence)),
                "error": blocked_reason,
                "observations": [],
            },
        )
        self.ledger.record(
            "brain.tool.execution_planned",
            session_id=request.session_id,
            payload={
                "execution_id": execution_id,
                "tool_id": request.tool_id,
                "action": request.action,
                "status": status,
                "dry_run": request.dry_run,
                "decision": decision,
            },
        )

        if status in {"blocked", "awaiting_approval"}:
            return self._result_from_checkpoint(checkpoint)

        return self._run(checkpoint_id, request)

    def resume(
        self,
        checkpoint_id: str,
        request: ExecutionRequest,
    ) -> ExecutionResult:
        """Resume an interrupted/failed/approval checkpoint with a fresh payload.

        The caller must resupply request payload because checkpoints persist only
        redacted input. This prevents secrets from being recoverable from disk.
        """
        checkpoint = self.checkpoints.get(checkpoint_id)
        if checkpoint.get("tool_id") != request.tool_id or checkpoint.get("action") != request.action:
            raise ValueError("resume request does not match checkpoint tool action")
        if checkpoint.get("session_id") != request.session_id:
            raise ValueError("resume request does not match checkpoint session")
        if checkpoint.get("status") == "completed":
            return self._result_from_checkpoint(checkpoint, reused=True)

        tool = self.tools.get(request.tool_id)
        decision = self._decision(tool, request)
        approval_required = decision.get("decision") == "approval_required"
        if decision.get("decision") == "blocked":
            updated = self.checkpoints.save(
                checkpoint_id,
                {"status": "blocked", "decision": decision, "error": decision.get("reason")},
            )
            return self._result_from_checkpoint(updated)
        if approval_required and not request.approved:
            updated = self.checkpoints.save(
                checkpoint_id,
                {"status": "awaiting_approval", "decision": decision, "approval_required": True},
            )
            return self._result_from_checkpoint(updated)

        self.checkpoints.save(
            checkpoint_id,
            {
                "decision": decision,
                "approval_required": approval_required,
                "dry_run": request.dry_run,
                "safe_payload": redact_sensitive(dict(request.payload)),
                "safe_evidence": redact_sensitive(dict(request.evidence)),
                "recovery_required": False,
            },
        )
        return self._run(checkpoint_id, request)

    def _run(self, checkpoint_id: str, request: ExecutionRequest) -> ExecutionResult:
        tool = self.tools.get(request.tool_id)
        max_attempts = self.max_attempts if tool.idempotent else 1
        observations: list[dict[str, Any]] = list(
            self.checkpoints.get(checkpoint_id).get("observations") or []
        )
        starting_attempt = int(self.checkpoints.get(checkpoint_id).get("attempts") or 0)

        with self._lock:
            self.checkpoints.save(checkpoint_id, {"status": "running"})
            for offset in range(1, max_attempts + 1):
                attempt = starting_attempt + offset
                try:
                    output = self.tools.invoke(
                        request.tool_id,
                        request.action,
                        request.payload,
                        dry_run=request.dry_run,
                    )
                    observation = ExecutionObservation(
                        execution_id=str(self.checkpoints.get(checkpoint_id)["execution_id"]),
                        attempt=attempt,
                        status="completed",
                        timestamp=time.time(),
                        output=redact_sensitive(output),
                    )
                    observations.append(asdict(observation))
                    checkpoint = self.checkpoints.save(
                        checkpoint_id,
                        {
                            "status": "completed",
                            "attempts": attempt,
                            "output": redact_sensitive(output),
                            "error": None,
                            "error_type": None,
                            "observations": observations,
                            "recovery_required": False,
                        },
                    )
                    self.ledger.record(
                        "brain.tool.execution_completed",
                        session_id=request.session_id,
                        payload={
                            "execution_id": checkpoint["execution_id"],
                            "tool_id": request.tool_id,
                            "action": request.action,
                            "attempt": attempt,
                            "output": redact_sensitive(output),
                        },
                    )
                    return self._result_from_checkpoint(checkpoint)
                except Exception as exc:  # adapters are external trust boundaries
                    observation = ExecutionObservation(
                        execution_id=str(self.checkpoints.get(checkpoint_id)["execution_id"]),
                        attempt=attempt,
                        status="failed",
                        timestamp=time.time(),
                        error_type=type(exc).__name__,
                        error=str(exc),
                    )
                    observations.append(asdict(observation))
                    terminal = offset >= max_attempts
                    checkpoint = self.checkpoints.save(
                        checkpoint_id,
                        {
                            "status": "failed" if terminal else "retrying",
                            "attempts": attempt,
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                            "observations": observations,
                            "recovery_required": terminal,
                        },
                    )
                    self.ledger.record(
                        "brain.tool.execution_failed" if terminal else "brain.tool.execution_retry",
                        session_id=request.session_id,
                        payload={
                            "execution_id": checkpoint["execution_id"],
                            "tool_id": request.tool_id,
                            "action": request.action,
                            "attempt": attempt,
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                        },
                    )
                    if terminal:
                        return self._result_from_checkpoint(checkpoint)

        raise RuntimeError("unreachable execution state")

    def _result_from_checkpoint(self, checkpoint: Mapping[str, Any], *, reused: bool = False) -> ExecutionResult:
        observations = tuple(
            ExecutionObservation(
                execution_id=str(item.get("execution_id") or checkpoint.get("execution_id")),
                attempt=int(item.get("attempt") or 0),
                status=str(item.get("status") or "unknown"),
                timestamp=float(item.get("timestamp") or 0.0),
                output=item.get("output") if isinstance(item.get("output"), Mapping) else None,
                error_type=str(item.get("error_type")) if item.get("error_type") else None,
                error=str(item.get("error")) if item.get("error") else None,
            )
            for item in (checkpoint.get("observations") or [])
            if isinstance(item, Mapping)
        )
        output = checkpoint.get("output")
        return ExecutionResult(
            execution_id=str(checkpoint.get("execution_id") or checkpoint.get("checkpoint_id")),
            checkpoint_id=str(checkpoint.get("checkpoint_id")),
            session_id=str(checkpoint.get("session_id")),
            tool_id=str(checkpoint.get("tool_id")),
            action=str(checkpoint.get("action")),
            status=str(checkpoint.get("status")),
            attempts=int(checkpoint.get("attempts") or 0),
            approval_required=bool(checkpoint.get("approval_required")),
            dry_run=bool(checkpoint.get("dry_run")),
            reused=reused,
            decision=checkpoint.get("decision") if isinstance(checkpoint.get("decision"), Mapping) else {},
            output=output if isinstance(output, Mapping) else None,
            error_type=str(checkpoint.get("error_type")) if checkpoint.get("error_type") else None,
            error=str(checkpoint.get("error")) if checkpoint.get("error") else None,
            observations=observations,
        )

    def dashboard(self) -> dict[str, Any]:
        checkpoints = self.checkpoints.list()
        return {
            "controller": "permissioned_tool_execution",
            "max_attempts": self.max_attempts,
            "checkpoint_count": len(checkpoints),
            "running": sum(1 for item in checkpoints if item.get("status") == "running"),
            "awaiting_approval": sum(1 for item in checkpoints if item.get("status") == "awaiting_approval"),
            "completed": sum(1 for item in checkpoints if item.get("status") == "completed"),
            "failed": sum(1 for item in checkpoints if item.get("status") == "failed"),
            "interrupted": sum(1 for item in checkpoints if item.get("status") == "interrupted"),
            "secret_persistence": "redacted_only",
            "write_policy": "explicit_approval",
            "retry_policy": "bounded_idempotent_only",
        }
