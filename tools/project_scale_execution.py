"""Scale execution proof over the existing shared Research OS core.

This harness exercises real ProjectDefinition/ProjectRegistry instances at
10/20/50/100 projects through the existing capability executor and shared
append-only evidence plane. It creates no runtime, queue, scheduler, authority,
or project-local ledger.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from tools.project_execution import ProjectExecutionProof, ProjectExecutionResult
from tools.project_registry import ProjectRegistry
from v3.research_os_v3.resource_lineage import (
    ConflictEvidence,
    ResourceConflictError,
    ResourceVersionStore,
    release_and_reconcile_on_conflict,
)

SCALE_LEVELS = (10, 20, 50, 100)


@dataclass(frozen=True)
class ScaleExecutionSummary:
    project_count: int
    completed: int
    recovered: int
    evidence_records: int


class AgentExecutor:
    """Minimal adapter used only to prove the canonical agent operation path."""

    def run(self, request: str) -> str:
        return f"ran:{request}"


def execute_scale(
    *,
    registry: ProjectRegistry,
    ledger_path: Path,
    owner_id: str,
    source_sha: str,
    target_sha: str,
    workflow_run_id: str,
    executor_factory: Callable[[], object] = AgentExecutor,
) -> ScaleExecutionSummary:
    from tools.lifecycle_evidence import LifecycleEvidenceLedger
    from tools.runtime_evidence import capture_runtime_evidence

    ledger = LifecycleEvidenceLedger(ledger_path)
    proof = ProjectExecutionProof(
        registry=registry,
        ledger=ledger,
        owner_id=owner_id,
        source_sha=source_sha,
        target_sha=target_sha,
        workflow_run_id=workflow_run_id,
    )
    completed = 0
    recovered = 0

    for index, project in enumerate(registry.all(), start=1):
        correlation_id = f"{project.project_id}-scale-{index:03d}"
        result: ProjectExecutionResult = proof.invoke(
            project_id=project.project_id,
            capability_id="agent",
            action="run agent",
            executor=executor_factory(),
            args=(f"scale-{project.project_id}",),
            correlation_id=correlation_id,
            authorized=True,
        )
        if result.status == "complete":
            completed += 1
        elif result.status == "recover":
            recovered += 1
        else:
            raise AssertionError(f"unknown execution status: {result.status}")

        snapshot = capture_runtime_evidence(
            ledger,
            project_id=project.project_id,
            correlation_id=correlation_id,
            expected_source_sha=source_sha,
        )
        if snapshot.terminal_state != "COMPLETE":
            raise AssertionError(
                f"{project.project_id}: expected COMPLETE, got {snapshot.terminal_state}"
            )
        if not snapshot.records or any(
            record.project_id != project.project_id for record in snapshot.records
        ):
            raise AssertionError(f"{project.project_id}: evidence crossed project boundary")

    return ScaleExecutionSummary(
        project_count=len(registry.all()),
        completed=completed,
        recovered=recovered,
        evidence_records=len(ledger.read()),
    )


def exercise_resource_conflict(
    path: Path,
    *,
    release_resources: Callable[[], None],
    reconcile_delivery: Callable[[ConflictEvidence], None],
) -> ConflictEvidence:
    """Prove stale-SHA rejection and the existing release/reconcile path."""
    store = ResourceVersionStore(path)
    initial = store.initialize("project-001-resource", {"version": 1})
    current = store.update(
        "project-001-resource",
        expected_version=initial.version,
        expected_sha256=initial.content_sha256,
        content={"version": 2},
    )

    released = {"value": False}
    reconciled = {"value": False}

    def release() -> None:
        released["value"] = True
        release_resources()

    def reconcile(evidence: ConflictEvidence) -> None:
        reconciled["value"] = True
        reconcile_delivery(evidence)

    try:
        store.update(
            "project-001-resource",
            expected_version=initial.version,
            expected_sha256=initial.content_sha256,
            content={"version": 3},
        )
    except ResourceConflictError as exc:
        evidence = exc.evidence
        release_and_reconcile_on_conflict(
            evidence,
            release_resources=release,
            reconcile_delivery=reconcile,
        )
        if not released["value"] or not reconciled["value"]:
            raise AssertionError("resource conflict did not release and reconcile")
        if evidence.actual_version != current.version:
            raise AssertionError("conflict evidence lost the actual resource version")
        if evidence.actual_sha256 != current.content_sha256:
            raise AssertionError("conflict evidence lost the actual resource SHA")
        return evidence

    raise AssertionError("stale resource mutation was not rejected")


__all__ = [
    "SCALE_LEVELS",
    "AgentExecutor",
    "ScaleExecutionSummary",
    "execute_scale",
    "exercise_resource_conflict",
]
