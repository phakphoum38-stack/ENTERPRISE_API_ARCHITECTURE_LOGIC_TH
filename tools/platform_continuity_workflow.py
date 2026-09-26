"""Platform continuity bridge over the existing Workflow/Queue/Runner primitives.

This is an integration boundary, not a new runtime. It validates a persisted
work checkpoint, dispatches its task through the existing durable queue and
stateless runner, binds execution evidence to the checkpoint source SHA, and
builds a successor handoff payload without granting authorization or release
authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from tools.lifecycle_evidence import LifecycleEvidence, LifecycleEvidenceLedger
from tools.platform_work_checkpoint import (
    create_checkpoint,
    get_checkpoint,
    resume_checkpoint,
)
from v3.research_os_v3.queue import DurableTaskQueue, QueueTask
from v3.research_os_v3.runner import RunnerResult, StatelessResearchRunner

EventSink = Callable[[str, str, dict[str, Any]], None]


@dataclass(frozen=True)
class ContinuityDispatchResult:
    checkpoint_id: str
    task_id: str
    status: str
    runner_status: str
    successor_checkpoint_id: str | None
    evidence_refs: tuple[str, ...]


def build_successor_handoff(
    *,
    repository: str,
    canonical_sha: str,
    protected_baseline_sha: str,
    active_work: list[str],
    deferred_work: list[str],
    decisions: list[str],
    verified_truths: list[str],
    evidence_refs: list[str],
    open_risks: list[str],
    assumptions: list[str],
    unknowns: list[str],
    authority_boundaries: list[str],
    tooling_state: list[str],
    active_mission: str,
    next_permitted_action: str,
    forbidden_actions: list[str],
) -> dict[str, Any]:
    """Build a successor handoff without persisting or granting authority."""
    return {
        "repository": repository,
        "canonical_sha": canonical_sha,
        "protected_baseline_sha": protected_baseline_sha,
        "active_work": list(active_work),
        "deferred_work": list(deferred_work),
        "decisions": list(decisions),
        "verified_truths": list(verified_truths),
        "evidence_refs": list(evidence_refs),
        "open_risks": list(open_risks),
        "assumptions": list(assumptions),
        "unknowns": list(unknowns),
        "authority_boundaries": list(authority_boundaries),
        "tooling_state": list(tooling_state),
        "active_mission": active_mission,
        "next_permitted_action": next_permitted_action,
        "forbidden_actions": list(forbidden_actions),
        "successor_requires_context_recovery": True,
        "successor_requires_reverification": True,
        "inherits_certification": False,
    }


def dispatch_checkpoint(
    *,
    owner_id: str,
    checkpoint_id: str,
    queue: DurableTaskQueue,
    runner: StatelessResearchRunner,
    ledger: LifecycleEvidenceLedger,
    handler: Callable[[QueueTask], None],
    project_id: str = "",
) -> ContinuityDispatchResult:
    """Resume one verified checkpoint through the existing execution plane."""
    resume = resume_checkpoint(owner_id, checkpoint_id)
    if resume["status"] != "READY":
        raise ValueError("checkpoint is not resumable: " + ",".join(resume["failures"]))

    checkpoint = get_checkpoint(owner_id, checkpoint_id)
    correlation_id = f"continuity-{checkpoint_id}"
    evidence_refs: list[str] = []

    def record(event_type: str, task_id: str, detail: dict[str, Any]) -> None:
        state = {
            "runner.claimed": "OBSERVE",
            "runner.completed": "COMPLETE",
            "runner.retry": "OBSERVE",
            "runner.failed": "RECOVER",
        }.get(event_type)
        if state is None:
            return
        recovery = state == "RECOVER"
        record = LifecycleEvidence.create(
            correlation_id=correlation_id,
            capability_id="platform-continuity",
            action=event_type,
            state=state,
            owner_id=owner_id,
            source_sha=str(checkpoint["source_sha"]),
            target_sha=str(checkpoint["source_sha"]),
            workflow_run_id=checkpoint["task_id"],
            recovery_required=recovery,
            recovery_reason=event_type if recovery else None,
            project_id=project_id,
        )
        ledger.append(record)
        evidence_refs.append(record.event_id)

    runner_with_sink = StatelessResearchRunner(
        queue,
        max_attempts=runner.max_attempts,
        worker_id=runner.worker_id,
        event_sink=record,
    )
    queue.enqueue(
        QueueTask(
            checkpoint["task_id"],
            checkpoint["task_id"],
            {
                "checkpoint_id": checkpoint_id,
                "source_sha": checkpoint["source_sha"],
                "current_step": checkpoint["current_step"],
                "context_refs": checkpoint["context_refs"],
                "evidence_refs": checkpoint["evidence_refs"],
            },
        )
    )
    result = runner_with_sink.run_once(handler)
    if result is None:
        raise RuntimeError("checkpoint dispatch produced no runner result")
    while result.status == "retry":
        result = runner_with_sink.run_once(handler)
        if result is None:
            raise RuntimeError("retrying checkpoint dispatch produced no runner result")

    terminal_state = "COMPLETED" if result.status == "completed" else "DEFERRED"
    successor = create_checkpoint(
        owner_id=owner_id,
        task_id=checkpoint["task_id"],
        workflow_state=terminal_state,
        current_step=(
            "completed:" + checkpoint["current_step"]
            if result.status == "completed"
            else "recovery:" + checkpoint["current_step"]
        )[:512],
        completed_steps=checkpoint["completed_steps"] + (
            [checkpoint["current_step"]] if result.status == "completed" else []
        ),
        pending_steps=[] if result.status == "completed" else checkpoint["pending_steps"],
        evidence_refs=checkpoint["evidence_refs"] + evidence_refs,
        deferred_work=checkpoint["deferred_work"] if result.status == "completed" else (
            checkpoint["deferred_work"] + ["runner_recovery_required"]
        ),
        context_refs=checkpoint["context_refs"],
        next_action="final_gate_reverify" if result.status == "completed" else "recover_then_resume",
        source_sha=checkpoint["source_sha"],
        supersedes=checkpoint_id,
    )
    return ContinuityDispatchResult(
        checkpoint_id=checkpoint_id,
        task_id=checkpoint["task_id"],
        status="COMPLETED" if result.status == "completed" else "DEFERRED",
        runner_status=result.status,
        successor_checkpoint_id=str(successor["checkpoint_id"]),
        evidence_refs=tuple(evidence_refs),
    )


__all__ = [
    "ContinuityDispatchResult",
    "build_successor_handoff",
    "dispatch_checkpoint",
]
