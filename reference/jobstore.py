from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any
from uuid import uuid4


class JobConflict(Exception):
    pass


class LeaseConflict(Exception):
    pass


@dataclass
class Job:
    job_id: str
    workflow_id: str
    idempotency_key: str
    payload: dict[str, Any]
    status: str = "QUEUED"
    attempts: int = 0
    max_attempts: int = 3
    lease_id: str | None = None
    lease_owner: str | None = None
    lease_expires_at: datetime | None = None


class InMemoryJobStore:
    """Deterministic reference implementation of JobStore lease semantics."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._jobs: dict[str, Job] = {}
        self._idempotency: dict[tuple[str, str], str] = {}

    def create(self, workflow_id: str, idempotency_key: str, payload: dict[str, Any], max_attempts: int = 3) -> Job:
        with self._lock:
            key = (workflow_id, idempotency_key)
            existing = self._idempotency.get(key)
            if existing:
                return self._jobs[existing]
            job = Job(str(uuid4()), workflow_id, idempotency_key, payload, max_attempts=max_attempts)
            self._jobs[job.job_id] = job
            self._idempotency[key] = job.job_id
            return job

    def claim(self, job_id: str, runner_id: str, lease_seconds: int = 60) -> Job:
        now = datetime.now(timezone.utc)
        with self._lock:
            job = self._jobs[job_id]
            if job.status not in {"QUEUED", "RETRYING", "CLAIMED", "RUNNING"}:
                raise JobConflict("job is not runnable")
            if job.lease_expires_at and job.lease_expires_at > now:
                raise LeaseConflict("job already has an active lease")
            job.lease_id = str(uuid4())
            job.lease_owner = runner_id
            job.lease_expires_at = now + timedelta(seconds=lease_seconds)
            job.status = "CLAIMED"
            return job

    def heartbeat(self, job_id: str, lease_id: str, lease_seconds: int = 60) -> Job:
        with self._lock:
            job = self._jobs[job_id]
            self._assert_lease(job, lease_id)
            job.lease_expires_at = datetime.now(timezone.utc) + timedelta(seconds=lease_seconds)
            return job

    def complete(self, job_id: str, lease_id: str) -> Job:
        with self._lock:
            job = self._jobs[job_id]
            self._assert_lease(job, lease_id)
            job.status = "SUCCEEDED"
            job.lease_id = None
            job.lease_owner = None
            job.lease_expires_at = None
            return job

    def fail(self, job_id: str, lease_id: str) -> Job:
        with self._lock:
            job = self._jobs[job_id]
            self._assert_lease(job, lease_id)
            job.attempts += 1
            job.status = "RETRYING" if job.attempts < job.max_attempts else "DEAD_LETTER"
            job.lease_id = None
            job.lease_owner = None
            job.lease_expires_at = None
            return job

    def _assert_lease(self, job: Job, lease_id: str) -> None:
        now = datetime.now(timezone.utc)
        if job.lease_id != lease_id or not job.lease_expires_at or job.lease_expires_at <= now:
            raise LeaseConflict("lease is stale or invalid")
