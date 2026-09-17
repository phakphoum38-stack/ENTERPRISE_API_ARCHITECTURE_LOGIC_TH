"""P1 execution-plane integration over the existing Research OS runtimes.

This adapter turns the P0 canonical identity/attempt contracts into concrete
bindings for the existing API and V3 execution planes. It does not create a
queue, scheduler, worker, state machine, retry engine, or execution engine.
Native runtime objects remain authoritative in their own plane.
"""

from __future__ import annotations
from dataclasses import dataclass

from .canonical_attempt_identity import CanonicalAttempt, first_attempt
from .canonical_execution_mapping import ExecutionBinding, bind_api_step, bind_v3_task
from .canonical_identity_federation import CanonicalIdentity

class P1ExecutionIntegrationError(ValueError):
    """Raised when an existing execution plane cannot be bound safely."""

@dataclass(frozen=True)
class IntegratedAttempt:
    """One canonical attempt plus its native execution-plane binding."""
    attempt: CanonicalAttempt
    binding: ExecutionBinding

    @property
    def identity(self) -> CanonicalIdentity:
        return self.binding.canonical

def _require_text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise P1ExecutionIntegrationError(f"{name} is required")
    return value.strip()

def bind_api_execution(*, identity: CanonicalIdentity, step: object, run_id: str, attempt_id: str, attempt_number: int = 1, retry_of: str | None = None) -> IntegratedAttempt:
    """Bind an existing API step/RuntimeTask to canonical attempt identity."""
    run_id = _require_text(run_id, "run_id")
    attempt_id = _require_text(attempt_id, "attempt_id")
    if identity.task_id is None:
        identity = identity.bind(task_id=_require_text(getattr(step, "step_id", None), "task_id"))
    if identity.run_id is not None and identity.run_id != run_id:
        raise P1ExecutionIntegrationError("API run_id conflicts with canonical run_id")
    if attempt_number == 1:
        if retry_of is not None:
            raise P1ExecutionIntegrationError("first API attempt cannot have retry_of")
        attempt = first_attempt(mission_id=identity.mission_id, work_id=identity.work_id, task_id=identity.task_id, run_id=run_id, attempt_id=attempt_id)
    else:
        if not retry_of:
            raise P1ExecutionIntegrationError("retry API attempt requires retry_of")
        attempt = CanonicalAttempt(identity.mission_id, identity.work_id, identity.task_id, run_id, attempt_id, attempt_number, retry_of)
    bound_identity = identity.bind(task_id=attempt.task_id, run_id=run_id)
    return IntegratedAttempt(attempt, bind_api_step(identity=bound_identity, step=step, attempt=attempt))

def bind_v3_execution(*, identity: CanonicalIdentity, research_task: object, queue_task: object, run_id: str, attempt_id: str, attempt_number: int = 1, retry_of: str | None = None) -> IntegratedAttempt:
    """Bind an existing V3 ResearchTask + QueueTask to canonical identity."""
    run_id = _require_text(run_id, "run_id")
    attempt_id = _require_text(attempt_id, "attempt_id")
    native_task_id = _require_text(getattr(queue_task, "task_id", None), "queue task id")
    if identity.task_id is None:
        identity = identity.bind(task_id=native_task_id)
    if identity.task_id != native_task_id:
        raise P1ExecutionIntegrationError("V3 queue task_id conflicts with canonical task_id")
    if identity.run_id is not None and identity.run_id != run_id:
        raise P1ExecutionIntegrationError("V3 run_id conflicts with canonical run_id")
    if attempt_number == 1:
        if retry_of is not None:
            raise P1ExecutionIntegrationError("first V3 attempt cannot have retry_of")
        attempt = first_attempt(mission_id=identity.mission_id, work_id=identity.work_id, task_id=native_task_id, run_id=run_id, attempt_id=attempt_id)
    else:
        if not retry_of:
            raise P1ExecutionIntegrationError("retry V3 attempt requires retry_of")
        attempt = CanonicalAttempt(identity.mission_id, identity.work_id, native_task_id, run_id, attempt_id, attempt_number, retry_of)
    bound_identity = identity.bind(task_id=native_task_id, run_id=run_id)
    return IntegratedAttempt(attempt, bind_v3_task(identity=bound_identity, research_task=research_task, queue_task=queue_task, attempt=attempt))

def assert_retry_pair(previous: IntegratedAttempt, current: IntegratedAttempt) -> None:
    """Fail closed unless current follows previous attempt lineage."""
    from .canonical_attempt_identity import assert_same_attempt_lineage
    assert_same_attempt_lineage(previous.attempt, current.attempt)
