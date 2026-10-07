from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Protocol


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RECLAIMABLE = "RECLAIMABLE"


class AssignmentStatus(str, Enum):
    RESERVED = "RESERVED"
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    RECLAIMED = "RECLAIMED"


@dataclass(frozen=True)
class JobRecord:
    job_id: str
    workflow_id: str
    status: JobStatus
    payload: dict[str, Any]
    attempt: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class AssignmentRecord:
    assignment_id: str
    job_id: str
    runner_id: str
    fencing_token: int
    status: AssignmentStatus
    lease_expires_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class RunnerRecord:
    runner_id: str
    status: str
    capabilities: frozenset[str]
    last_heartbeat: datetime
    updated_at: datetime


@dataclass(frozen=True)
class AttemptRecord:
    job_id: str
    attempt: int
    runner_id: str
    assignment_id: str
    fencing_token: int
    started_at: datetime
    finished_at: datetime | None
    status: str
    result: dict[str, Any] | None


class DurablePersistence(Protocol):
    """Storage boundary. Implementations must provide atomic reservation/fencing."""

    def get_job(self, job_id: str) -> JobRecord | None: ...

    def reserve_assignment(
        self, job_id: str, runner_id: str, lease_expires_at: datetime | None
    ) -> AssignmentRecord: ...

    def renew_assignment(
        self, job_id: str, assignment_id: str, fencing_token: int,
        lease_expires_at: datetime
    ) -> AssignmentRecord: ...

    def complete_assignment(
        self, job_id: str, assignment_id: str, fencing_token: int,
        status: JobStatus, result: dict[str, Any] | None = None
    ) -> AssignmentRecord: ...

    def reclaim_expired_assignment(self, job_id: str) -> AssignmentRecord | None: ...
