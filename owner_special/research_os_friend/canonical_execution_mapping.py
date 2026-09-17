"""P0-3 adapters mapping existing execution planes to canonical identity.

No execution engine or queue is introduced here. Native AEOS/API/V3/Friend
objects remain authoritative in their own plane. This module only creates
immutable mapping records so those objects can be correlated safely.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .canonical_identity_federation import CanonicalIdentity, CanonicalIdentityError
from .canonical_attempt_identity import CanonicalAttempt


class ExecutionMappingError(CanonicalIdentityError):
    """Raised when native execution identity cannot be mapped safely."""


@dataclass(frozen=True)
class ExecutionBinding:
    plane: str
    native_task_id: str
    native_run_id: str | None
    canonical: CanonicalIdentity
    native_step_id: str | None = None
    native_attempt_id: str | None = None

    def __post_init__(self) -> None:
        if not self.plane.strip():
            raise ExecutionMappingError("plane is required")
        if not self.native_task_id.strip():
            raise ExecutionMappingError("native_task_id is required")
        if self.native_run_id is not None and not self.native_run_id.strip():
            raise ExecutionMappingError("native_run_id must be non-empty")
        if self.native_step_id is not None and not self.native_step_id.strip():
            raise ExecutionMappingError("native_step_id must be non-empty")
        if self.native_attempt_id is not None and not self.native_attempt_id.strip():
            raise ExecutionMappingError("native_attempt_id must be non-empty")

        if self.canonical.task_id is None:
            raise ExecutionMappingError("canonical task_id is required")
        if self.canonical.run_id is None:
            raise ExecutionMappingError("canonical run_id is required")
        if self.native_run_id is not None and self.native_run_id != self.canonical.run_id:
            raise ExecutionMappingError("native run_id does not match canonical run_id")
        if self.native_attempt_id is not None and self.canonical.attempt_id != self.native_attempt_id:
            raise ExecutionMappingError("native attempt_id does not match canonical attempt_id")

    @property
    def is_retry_binding(self) -> bool:
        return self.canonical.attempt_id is not None


def _value(source: Any, key: str) -> Any:
    if isinstance(source, dict):
        return source.get(key)
    return getattr(source, key, None)


def _required(source: Any, key: str) -> str:
    value = _value(source, key)
    if not isinstance(value, str) or not value.strip():
        raise ExecutionMappingError(f"{key} is required for execution mapping")
    return value.strip()


def bind_api_step(
    *,
    identity: CanonicalIdentity,
    step: Any,
    attempt: CanonicalAttempt,
) -> ExecutionBinding:
    """Map an API DelegatedStep/RuntimeTask retry to canonical identity.

    API orchestration may create a new native task_id for each retry. The
    canonical task/run remain stable while native_task_id records that
    implementation detail.
    """

    if attempt.task_id != identity.task_id or attempt.run_id != identity.run_id:
        raise ExecutionMappingError("API attempt does not match canonical task/run")
    native_task_id = _required(step, "task_id")
    step_id = _value(step, "step_id")
    return ExecutionBinding(
        plane="api",
        native_task_id=native_task_id,
        native_run_id=attempt.run_id,
        canonical=identity.bind(
            task_id=attempt.task_id,
            run_id=attempt.run_id,
            attempt_id=attempt.attempt_id,
        ),
        native_step_id=step_id,
        native_attempt_id=attempt.attempt_id,
    )


def bind_v3_task(
    *,
    identity: CanonicalIdentity,
    research_task: Any,
    queue_task: Any,
    attempt: CanonicalAttempt,
) -> ExecutionBinding:
    """Map V3 ResearchTask + QueueTask to canonical identity.

    V3 currently retains one native task_id while its retry counter changes.
    The canonical attempt therefore carries the unique attempt identity while
    native_task_id remains the stable queue task identifier.
    """

    if attempt.task_id != identity.task_id or attempt.run_id != identity.run_id:
        raise ExecutionMappingError("V3 attempt does not match canonical task/run")
    native_task_id = _required(queue_task, "task_id")
    planner_task_id = _required(research_task, "id")
    return ExecutionBinding(
        plane="v3",
        native_task_id=native_task_id,
        native_run_id=attempt.run_id,
        canonical=identity.bind(
            task_id=attempt.task_id,
            run_id=attempt.run_id,
            attempt_id=attempt.attempt_id,
        ),
        native_step_id=planner_task_id,
        native_attempt_id=attempt.attempt_id,
    )


def bind_friend_run(
    *,
    identity: CanonicalIdentity,
    agent_run: Any,
    attempt: CanonicalAttempt,
) -> ExecutionBinding:
    """Map the existing Friend AgentRun without replacing its run identity."""

    if attempt.task_id != identity.task_id or attempt.run_id != identity.run_id:
        raise ExecutionMappingError("Friend attempt does not match canonical task/run")
    native_run_id = _required(agent_run, "run_id")
    if native_run_id != attempt.run_id:
        raise ExecutionMappingError("Friend native run_id does not match canonical run_id")
    return ExecutionBinding(
        plane="friend",
        native_task_id=attempt.task_id,
        native_run_id=native_run_id,
        canonical=identity.bind(
            task_id=attempt.task_id,
            run_id=native_run_id,
            attempt_id=attempt.attempt_id,
        ),
        native_attempt_id=attempt.attempt_id,
    )


def bind_aeos_work(
    *,
    identity: CanonicalIdentity,
    work_item: Any,
    task_id: str,
    run_id: str,
    attempt: CanonicalAttempt,
) -> ExecutionBinding:
    """Map an existing AEOS WorkItem to a canonical execution task/run."""

    work_id = _required(work_item, "work_id")
    mission_id = _required(work_item, "mission_id")
    baseline_sha = _required(work_item, "baseline_sha")
    if work_id != identity.work_id or mission_id != identity.mission_id:
        raise ExecutionMappingError("AEOS work lineage does not match canonical identity")
    if baseline_sha != identity.baseline_sha:
        raise ExecutionMappingError("AEOS baseline SHA does not match canonical identity")
    if attempt.task_id != task_id or attempt.run_id != run_id:
        raise ExecutionMappingError("AEOS attempt does not match supplied task/run")

    bound = identity.bind(
        task_id=task_id,
        run_id=run_id,
        attempt_id=attempt.attempt_id,
    )
    return ExecutionBinding(
        plane="aeos",
        native_task_id=task_id,
        native_run_id=run_id,
        canonical=bound,
        native_attempt_id=attempt.attempt_id,
    )
