"""Phase C end-to-end binding from an authorized command to an existing executor.

This adapter is deliberately thin. It does not become a runtime, scheduler,
authorization authority, or release authority. Authorization must already have
been established by the canonical boundary. The adapter resolves only the
operation declared in capability_delegation.py, invokes that existing executor,
and records the lifecycle observation/evidence required by Phase B.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from tools.capability_delegation import DelegationOperation, get_operation
from tools.lifecycle_evidence import LifecycleEvidence, LifecycleEvidenceLedger


class CapabilityBindingError(RuntimeError):
    """Raised when a Phase C binding cannot be safely completed."""


@dataclass(frozen=True)
class BindingResult:
    capability_id: str
    action: str
    correlation_id: str
    status: str
    observation: Any = None
    recovery_reason: str | None = None


class CapabilityE2EBinding:
    """Execute one canonical delegated operation after external authorization."""

    def __init__(
        self,
        *,
        ledger: LifecycleEvidenceLedger,
        owner_id: str,
        source_sha: str,
        target_sha: str,
        workflow_run_id: str,
        project_id: str = "",
        contract_version: str = "research-os-phase-c-capability-e2e/v1",
    ) -> None:
        self.ledger = ledger
        self.owner_id = owner_id
        self.source_sha = source_sha
        self.target_sha = target_sha
        self.workflow_run_id = workflow_run_id
        self.contract_version = contract_version

    def invoke(
        self,
        *,
        capability_id: str,
        action: str,
        executor: object,
        args: tuple[Any, ...] = (),
        kwargs: Mapping[str, Any] | None = None,
        correlation_id: str,
        authorized: bool,
        project_id: str | None = None,
    ) -> BindingResult:
        """Invoke an existing executor and project its observation into evidence.

        authorized is supplied by the canonical authorization boundary; this
        class never grants authorization. A false value fails before execution.
        """
        kwargs = dict(kwargs or {})
        if project_id is not None and not project_id.strip():
            raise ValueError("project_id cannot be blank")
        self._record(correlation_id, capability_id, action, "INTENT", project_id=project_id or "")

        try:
            operation = get_operation(capability_id, action)
            self._record(correlation_id, capability_id, action, "VALIDATE", project_id=project_id or "")
            self._validate_sha()
            method = self._resolve_executor(executor, operation)

            self._record(correlation_id, capability_id, action, "PREPARE", project_id=project_id or "")
            if not authorized:
                raise CapabilityBindingError("external authorization is required")
            self._record(correlation_id, capability_id, action, "AUTHORIZE", project_id=project_id or "")

            observation = method(*args, **kwargs)

            self._record(correlation_id, capability_id, action, "EXECUTE", project_id=project_id or "")
            self._record(correlation_id, capability_id, action, "OBSERVE", project_id=project_id or "")
            self._record(correlation_id, capability_id, action, "EVIDENCE", project_id=project_id or "")
            self._record(correlation_id, capability_id, action, "COMPLETE", project_id=project_id or "")

            return BindingResult(
                capability_id=capability_id,
                action=action,
                correlation_id=correlation_id,
                status="complete",
                observation=observation,
            )
        except Exception as exc:
            reason = type(exc).__name__ + (f": {exc}" if str(exc) else "")
            self._record(
                correlation_id,
                capability_id,
                action,
                "RECOVER",
                recovery_required=True,
                recovery_reason=reason,
                project_id=project_id or "",
            )
            return BindingResult(
                capability_id=capability_id,
                action=action,
                correlation_id=correlation_id,
                status="recover",
                recovery_reason=reason,
            )

    def _resolve_executor(self, executor: object, operation: DelegationOperation) -> Any:
        method = getattr(executor, operation.executor_method, None)
        if method is None or not callable(method):
            raise CapabilityBindingError(
                f"executor does not expose canonical method: {operation.executor_method}"
            )
        return method

    def _validate_sha(self) -> None:
        for name, value in (("source_sha", self.source_sha), ("target_sha", self.target_sha)):
            if not isinstance(value, str) or len(value) != 40:
                raise CapabilityBindingError(f"{name} must be an exact commit SHA")

    def _record(
        self,
        correlation_id: str,
        capability_id: str,
        action: str,
        state: str,
        *,
        project_id: str = "",
        recovery_required: bool = False,
        recovery_reason: str | None = None,
    ) -> None:
        self.ledger.append(
            LifecycleEvidence.create(
                correlation_id=correlation_id,
                capability_id=capability_id,
                action=action,
                state=state,
                owner_id=self.owner_id,
                source_sha=self.source_sha,
                target_sha=self.target_sha,
                workflow_run_id=self.workflow_run_id,
                contract_version=self.contract_version,
                recovery_required=recovery_required,
                recovery_reason=recovery_reason,
                project_id=project_id,
            )
        )


__all__ = ["BindingResult", "CapabilityBindingError", "CapabilityE2EBinding"]
