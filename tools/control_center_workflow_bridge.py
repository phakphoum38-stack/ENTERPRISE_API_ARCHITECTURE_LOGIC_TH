#!/usr/bin/env python3
"""Bind the canonical workflow adapter to the existing Control Center kernel.

This module composes existing components; it does not create a new authority,
evidence store, scheduler, or workflow engine. The caller supplies the human
authorization decision when LIVE execution is requested.
"""
from __future__ import annotations

from dataclasses import dataclass

from .native_control_center import ControlCommand, NativeControlCenter
from .workflow_execution_adapter import (
    GitHubWorkflowExecutionAdapter,
    WorkflowExecutionObservation,
    WorkflowExecutionRequest,
)
from .workflow_resolver import ResolvedWorkflow


@dataclass(frozen=True)
class ControlCenterWorkflowResult:
    command_fingerprint: str
    resolution_fingerprint: str
    observation: WorkflowExecutionObservation
    evidence_ref: str | None


class ControlCenterWorkflowBridge:
    """Compose command preparation, workflow execution, and activity recording."""

    def __init__(
        self,
        control_center: NativeControlCenter,
        adapter: GitHubWorkflowExecutionAdapter,
    ) -> None:
        self.control_center = control_center
        self.adapter = adapter

    def execute(
        self,
        *,
        command: ControlCommand,
        resolution: ResolvedWorkflow,
        repository: str,
        target_sha: str,
        mode: str,
        inputs: dict[str, str] | None = None,
        authorized: bool = False,
    ) -> ControlCenterWorkflowResult:
        command_fingerprint = self.control_center.prepare(command)

        if mode == "LIVE":
            self.control_center.record_authorization(command.command_id, authorized)

        observation = self.adapter.execute(
            WorkflowExecutionRequest(
                resolution=resolution,
                repository=repository,
                target_sha=target_sha,
                mode=mode,
                inputs=inputs or {},
                authorized=authorized,
            )
        )

        evidence_ref = None
        if observation.run_id is not None:
            evidence_ref = (
                f"github-actions://{repository}/runs/"
                f"{observation.run_id}@{observation.target_sha}"
            )

        if mode == "LIVE":
            success = (
                observation.status == "completed"
                and observation.conclusion == "success"
                and observation.observed_head_sha == target_sha
            )
            self.control_center.record_execution(
                command.command_id,
                success=success,
                evidence_ref=evidence_ref,
            )

        return ControlCenterWorkflowResult(
            command_fingerprint=command_fingerprint,
            resolution_fingerprint=resolution.resolution_fingerprint,
            observation=observation,
            evidence_ref=evidence_ref,
        )


__all__ = ["ControlCenterWorkflowBridge", "ControlCenterWorkflowResult"]
