"""Project-scoped execution proof over the existing shared execution/evidence plane.

This module is an adapter/proof boundary, not a runtime, scheduler, queue,
authorization authority, resource manager, or release authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from tools.capability_e2e_binding import BindingResult, CapabilityE2EBinding
from tools.lifecycle_evidence import LifecycleEvidenceLedger
from tools.project_registry import ProjectRegistry


@dataclass(frozen=True)
class ProjectExecutionResult:
    project_id: str
    capability_id: str
    action: str
    correlation_id: str
    status: str
    evidence_valid: bool
    observation: Any = None
    recovery_reason: str | None = None


class ProjectExecutionProof:
    """Bind project identity to an existing canonical capability executor."""

    def __init__(
        self,
        *,
        registry: ProjectRegistry,
        ledger: LifecycleEvidenceLedger,
        owner_id: str,
        source_sha: str,
        target_sha: str,
        workflow_run_id: str,
    ) -> None:
        self.registry = registry
        self.ledger = ledger
        self._binding = CapabilityE2EBinding(
            ledger=ledger,
            owner_id=owner_id,
            source_sha=source_sha,
            target_sha=target_sha,
            workflow_run_id=workflow_run_id,
        )

    def invoke(
        self,
        *,
        project_id: str,
        capability_id: str,
        action: str,
        executor: object,
        correlation_id: str,
        authorized: bool,
        args: tuple[Any, ...] = (),
        kwargs: Mapping[str, Any] | None = None,
    ) -> ProjectExecutionResult:
        project = self.registry.get(project_id)
        if capability_id not in project.capabilities:
            raise ValueError(
                f"capability {capability_id!r} is not registered for project {project_id!r}"
            )

        self._binding.project_id = project_id
        result: BindingResult = self._binding.invoke(
            capability_id=capability_id,
            action=action,
            executor=executor,
            correlation_id=correlation_id,
            authorized=authorized,
            args=args,
            kwargs=kwargs,
        )
        errors = self.ledger.validate_chain(
            correlation_id=correlation_id,
            expected_source_sha=self._binding.source_sha,
            expected_project_id=project_id,
        )
        if errors:
            raise RuntimeError("project lifecycle evidence invalid: " + "; ".join(errors))

        return ProjectExecutionResult(
            project_id=project_id,
            capability_id=capability_id,
            action=action,
            correlation_id=correlation_id,
            status=result.status,
            evidence_valid=True,
            observation=result.observation,
            recovery_reason=result.recovery_reason,
        )


__all__ = ["ProjectExecutionProof", "ProjectExecutionResult"]
