"""Fail-closed identity primitives for governed Research OS verification.

This module is deliberately side-effect free: it captures and validates identity
records but never dispatches workflows, changes refs, approves releases, or
persists mutable evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import hashlib
import re
from typing import Any, Mapping


_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class IdentityState(str, Enum):
    WAITING_FOR_SHA = "WAITING_FOR_SHA"
    CAPTURED = "CAPTURED"
    VERIFYING = "VERIFYING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    STALE = "STALE"
    SHA_MISMATCH = "SHA_MISMATCH"
    CONFLICT = "CONFLICT"
    BLOCKED = "BLOCKED"
    TIMEOUT = "TIMEOUT"


class IdentityError(ValueError):
    """Raised when an identity transition would violate the contract."""


@dataclass(frozen=True)
class CapturedIdentity:
    """Immutable pipeline identity captured before downstream verification."""

    expected_sha: str
    captured_sha: str
    state: IdentityState
    run_correlation_id: str
    attempt: int = 0
    max_attempts: int = 3

    def __post_init__(self) -> None:
        for name, value in (("expected_sha", self.expected_sha), ("captured_sha", self.captured_sha)):
            if not _SHA_RE.fullmatch(value):
                raise IdentityError(f"{name} must be a 40-character lowercase commit SHA")
        if not self.run_correlation_id or len(self.run_correlation_id) > 256:
            raise IdentityError("run_correlation_id must be non-empty and bounded")
        if self.attempt < 0 or self.max_attempts < 1 or self.attempt > self.max_attempts:
            raise IdentityError("attempt/max_attempts are outside the bounded retry policy")
        if self.state == IdentityState.CAPTURED and self.expected_sha != self.captured_sha:
            raise IdentityError("CAPTURED identity must exactly match expected SHA")

    @classmethod
    def waiting(cls, expected_sha: str, run_correlation_id: str, *, attempt: int = 0, max_attempts: int = 3) -> "CapturedIdentity":
        return cls(expected_sha, expected_sha, IdentityState.WAITING_FOR_SHA, run_correlation_id, attempt, max_attempts)

    def capture(self, observed_sha: str) -> "CapturedIdentity":
        _validate_sha(observed_sha, "observed_sha")
        if self.state not in {IdentityState.WAITING_FOR_SHA}:
            raise IdentityError("identity can only be captured from WAITING_FOR_SHA")
        if observed_sha != self.expected_sha:
            return replace(self, captured_sha=observed_sha, state=IdentityState.SHA_MISMATCH)
        return replace(self, captured_sha=observed_sha, state=IdentityState.CAPTURED)

    def verify(self, observed_sha: str) -> "CapturedIdentity":
        _validate_sha(observed_sha, "observed_sha")
        if self.state != IdentityState.CAPTURED:
            raise IdentityError("verification requires CAPTURED identity")
        if observed_sha != self.captured_sha:
            return replace(self, state=IdentityState.SHA_MISMATCH)
        return replace(self, state=IdentityState.VERIFYING)

    def result(self, passed: bool) -> "CapturedIdentity":
        if self.state != IdentityState.VERIFYING:
            raise IdentityError("a verification result requires VERIFYING state")
        return replace(self, state=IdentityState.PASSED if passed else IdentityState.FAILED)

    def retry_wait(self) -> "CapturedIdentity":
        if self.state != IdentityState.WAITING_FOR_SHA:
            raise IdentityError("retry wait requires WAITING_FOR_SHA")
        next_attempt = self.attempt + 1
        if next_attempt >= self.max_attempts:
            return replace(self, attempt=self.max_attempts, state=IdentityState.TIMEOUT)
        return replace(self, attempt=next_attempt)


def _validate_sha(value: str, name: str = "sha") -> None:
    if not isinstance(value, str) or not _SHA_RE.fullmatch(value):
        raise IdentityError(f"{name} must be a 40-character lowercase commit SHA")


def lineage_id(source_sha: str, *stages: str) -> str:
    """Return a deterministic lineage identifier for a source and ordered stages."""
    _validate_sha(source_sha, "source_sha")
    if any(not isinstance(stage, str) or not stage or len(stage) > 256 for stage in stages):
        raise IdentityError("lineage stages must be non-empty bounded strings")
    material = "\n".join((source_sha, *stages)).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def evidence_is_fresh(evidence: Mapping[str, Any], captured_sha: str) -> bool:
    """Check that evidence is explicitly bound to the captured SHA.

    Missing or malformed identity fields are stale/unsafe, never implicitly fresh.
    """
    _validate_sha(captured_sha, "captured_sha")
    if not isinstance(evidence, Mapping):
        return False
    evidence_sha = evidence.get("commit_sha")
    if not isinstance(evidence_sha, str) or not _SHA_RE.fullmatch(evidence_sha):
        return False
    return evidence_sha == captured_sha


def bind_evidence(evidence: Mapping[str, Any], identity: CapturedIdentity) -> dict[str, Any]:
    """Return a bounded copy of evidence bound to an immutable captured identity."""
    if identity.state not in {IdentityState.CAPTURED, IdentityState.VERIFYING, IdentityState.PASSED}:
        raise IdentityError("evidence cannot bind to an unverified identity state")
    if not evidence_is_fresh(evidence, identity.captured_sha):
        raise IdentityError("stale or mismatched evidence is blocked")
    result = dict(evidence)
    result["commit_sha"] = identity.captured_sha
    result["run_correlation_id"] = identity.run_correlation_id
    return result
