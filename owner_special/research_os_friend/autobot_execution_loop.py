"""Bounded policy state machine for the Research OS Autobot execution loop.

The module models orchestration state only. It does not dispatch workflows,
mutate refs, execute shell/process actions, approve releases, merge changes,
or fabricate CI/evidence results.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import hashlib
import json
import re
from typing import Any, Mapping

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_CORRELATION_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_MAX_TEXT = 2048
_MAX_HISTORY = 64
_MAX_FAILURES = 32
_MAX_PAYLOAD = 64 * 1024


class AutobotExecutionError(ValueError):
    """Raised when an unsafe orchestration transition is requested."""


class ExecutionState(str, Enum):
    QUEUED = "QUEUED"
    DIAGNOSING = "DIAGNOSING"
    REPAIR_PLANNED = "REPAIR_PLANNED"
    REPAIRING = "REPAIRING"
    LOCAL_VERIFYING = "LOCAL_VERIFYING"
    SUBMITTED = "SUBMITTED"
    WAITING_FOR_CI = "WAITING_FOR_CI"
    CI_COMPLETED = "CI_COMPLETED"
    EVALUATING = "EVALUATING"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


_ALLOWED_TRANSITIONS = {
    ExecutionState.QUEUED: {ExecutionState.DIAGNOSING, ExecutionState.BLOCKED},
    ExecutionState.DIAGNOSING: {ExecutionState.REPAIR_PLANNED, ExecutionState.BLOCKED},
    ExecutionState.REPAIR_PLANNED: {ExecutionState.REPAIRING, ExecutionState.BLOCKED},
    ExecutionState.REPAIRING: {ExecutionState.LOCAL_VERIFYING, ExecutionState.BLOCKED},
    ExecutionState.LOCAL_VERIFYING: {ExecutionState.SUBMITTED, ExecutionState.BLOCKED},
    ExecutionState.SUBMITTED: {ExecutionState.WAITING_FOR_CI, ExecutionState.BLOCKED},
    ExecutionState.WAITING_FOR_CI: {ExecutionState.CI_COMPLETED, ExecutionState.BLOCKED},
    ExecutionState.CI_COMPLETED: {ExecutionState.EVALUATING, ExecutionState.BLOCKED},
    ExecutionState.EVALUATING: {ExecutionState.COMPLETED, ExecutionState.DIAGNOSING, ExecutionState.BLOCKED, ExecutionState.FAILED},
    ExecutionState.COMPLETED: set(),
    ExecutionState.BLOCKED: set(),
    ExecutionState.FAILED: set(),
}


@dataclass(frozen=True)
class ExecutionEvent:
    state: ExecutionState
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.state, ExecutionState):
            raise AutobotExecutionError("invalid execution state")
        _bounded_text(self.reason, "reason")


@dataclass(frozen=True)
class ExecutionJob:
    """Immutable bounded orchestration state bound to one source SHA."""

    job_id: str
    correlation_id: str
    source_sha: str
    state: ExecutionState = ExecutionState.QUEUED
    attempt: int = 0
    failure_fingerprints: tuple[str, ...] = ()
    events: tuple[ExecutionEvent, ...] = ()
    repair_commit_sha: str | None = None
    ci_run_id: str | None = None

    def __post_init__(self) -> None:
        _bounded_text(self.job_id, "job_id")
        if not _CORRELATION_RE.fullmatch(self.correlation_id):
            raise AutobotExecutionError("invalid correlation_id")
        _validate_sha(self.source_sha, "source_sha")
        if not isinstance(self.state, ExecutionState):
            raise AutobotExecutionError("invalid state")
        if not 0 <= self.attempt <= 20:
            raise AutobotExecutionError("attempt outside bound")
        if len(self.failure_fingerprints) > _MAX_FAILURES:
            raise AutobotExecutionError("failure fingerprint history exceeds bound")
        if len(self.events) > _MAX_HISTORY:
            raise AutobotExecutionError("event history exceeds bound")
        for fingerprint in self.failure_fingerprints:
            if not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
                raise AutobotExecutionError("invalid failure fingerprint")
        if self.repair_commit_sha is not None:
            _validate_sha(self.repair_commit_sha, "repair_commit_sha")
        if self.ci_run_id is not None:
            _bounded_text(self.ci_run_id, "ci_run_id")

    @classmethod
    def create(cls, job_id: str, correlation_id: str, source_sha: str) -> "ExecutionJob":
        return cls(job_id=job_id, correlation_id=correlation_id, source_sha=source_sha)

    def transition(self, state: ExecutionState, reason: str) -> "ExecutionJob":
        if state not in _ALLOWED_TRANSITIONS[self.state]:
            raise AutobotExecutionError(f"invalid transition {self.state.value} -> {state.value}")
        event = ExecutionEvent(state=state, reason=reason)
        return replace(self, state=state, events=self.events + (event,))

    def record_failure(self, failure: str) -> "ExecutionJob":
        _bounded_text(failure, "failure")
        fingerprint = hashlib.sha256(failure.strip().encode("utf-8")).hexdigest()
        if len(self.failure_fingerprints) >= _MAX_FAILURES:
            raise AutobotExecutionError("failure history bound exhausted")
        return replace(self, failure_fingerprints=self.failure_fingerprints + (fingerprint,))

    def bind_repair_commit(self, commit_sha: str) -> "ExecutionJob":
        _validate_sha(commit_sha, "repair commit SHA")
        if commit_sha == self.source_sha:
            raise AutobotExecutionError("repair commit must differ from source SHA")
        return replace(self, repair_commit_sha=commit_sha)

    def bind_ci_result(self, *, commit_sha: str, correlation_id: str, ci_run_id: str, passed: bool) -> "ExecutionJob":
        _validate_sha(commit_sha, "CI commit SHA")
        if correlation_id != self.correlation_id:
            raise AutobotExecutionError("CI correlation mismatch")
        _bounded_text(ci_run_id, "ci_run_id")
        expected_sha = self.repair_commit_sha or self.source_sha
        if commit_sha != expected_sha:
            raise AutobotExecutionError("stale or mismatched CI SHA")
        reason = "CI completed with authoritative result" if passed else "CI completed with failure evidence"
        return replace(self, ci_run_id=ci_run_id).transition(ExecutionState.EVALUATING, reason)

    def complete_from_ci(self, *, commit_sha: str, correlation_id: str, ci_run_id: str, passed: bool) -> "ExecutionJob":
        current = self.bind_ci_result(commit_sha=commit_sha, correlation_id=correlation_id, ci_run_id=ci_run_id, passed=passed)
        if not passed:
            return current.transition(ExecutionState.DIAGNOSING, "fresh CI failure requires diagnosis")
        return current.transition(ExecutionState.COMPLETED, "fresh CI evidence is authoritative")

    def fingerprint(self) -> str:
        payload = {
            "job_id": self.job_id,
            "correlation_id": self.correlation_id,
            "source_sha": self.source_sha,
            "state": self.state.value,
            "attempt": self.attempt,
            "failure_fingerprints": list(self.failure_fingerprints),
            "repair_commit_sha": self.repair_commit_sha,
            "ci_run_id": self.ci_run_id,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


def validate_job_payload(payload: Mapping[str, Any]) -> None:
    """Fail closed on oversized or authority-like orchestration payloads."""
    if not isinstance(payload, Mapping):
        raise AutobotExecutionError("payload must be a mapping")
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    if len(encoded) > _MAX_PAYLOAD:
        raise AutobotExecutionError("payload exceeds bound")
    blocked = ("approve", "merge", "release", "install", "dispatch", "credential", "secret", "token", "password", "private_key", "shell", "subprocess", "exec", "eval")
    lowered = json.dumps(payload, sort_keys=True, default=str).lower()
    if any(term in lowered for term in blocked):
        raise AutobotExecutionError("authority or execution content is not allowed")


def _validate_sha(value: str, name: str) -> None:
    if not isinstance(value, str) or not _SHA_RE.fullmatch(value):
        raise AutobotExecutionError(f"{name} must be a 40-character lowercase commit SHA")


def _bounded_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value or len(value) > _MAX_TEXT:
        raise AutobotExecutionError(f"{name} must be non-empty and bounded")
