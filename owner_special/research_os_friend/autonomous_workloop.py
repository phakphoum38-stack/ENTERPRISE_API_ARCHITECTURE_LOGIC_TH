"""Pure state-machine primitives for the AEOS autonomous workloop.

This module deliberately has no GitHub, filesystem, shell, network, merge, or
workflow-dispatch side effects. Integrations must supply independently observed
state and evidence to these functions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import re
from typing import Any, Mapping


class WorkloopError(ValueError):
    """Raised when a work item violates the AEOS lifecycle contract."""


class WorkState(str, Enum):
    MISSION_CREATED = "MISSION_CREATED"
    CONTRACTED = "CONTRACTED"
    PLANNED = "PLANNED"
    QUEUED = "QUEUED"
    LEASED = "LEASED"
    BRANCHED = "BRANCHED"
    DOCUMENTED = "DOCUMENTED"
    IMPLEMENTED = "IMPLEMENTED"
    DIFF_CAPTURED = "DIFF_CAPTURED"
    TESTED = "TESTED"
    CI_VERIFIED = "CI_VERIFIED"
    FORENSIC_VERIFIED = "FORENSIC_VERIFIED"
    REGRESSION_VERIFIED = "REGRESSION_VERIFIED"
    EVIDENCE_VERIFIED = "EVIDENCE_VERIFIED"
    PROVENANCE_VERIFIED = "PROVENANCE_VERIFIED"
    AUTHORITY_VERIFIED = "AUTHORITY_VERIFIED"
    CERTIFIED = "CERTIFIED"
    INTEGRATED = "INTEGRATED"
    MAIN_VERIFIED = "MAIN_VERIFIED"
    REANCHORED = "REANCHORED"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    QUARANTINED = "QUARANTINED"
    CANCELLED = "CANCELLED"


_PROGRESS = (
    WorkState.MISSION_CREATED,
    WorkState.CONTRACTED,
    WorkState.PLANNED,
    WorkState.QUEUED,
    WorkState.LEASED,
    WorkState.BRANCHED,
    WorkState.DOCUMENTED,
    WorkState.IMPLEMENTED,
    WorkState.DIFF_CAPTURED,
    WorkState.TESTED,
    WorkState.CI_VERIFIED,
    WorkState.FORENSIC_VERIFIED,
    WorkState.REGRESSION_VERIFIED,
    WorkState.EVIDENCE_VERIFIED,
    WorkState.PROVENANCE_VERIFIED,
    WorkState.AUTHORITY_VERIFIED,
    WorkState.CERTIFIED,
    WorkState.INTEGRATED,
    WorkState.MAIN_VERIFIED,
    WorkState.REANCHORED,
    WorkState.COMPLETED,
)
_INDEX = {state: index for index, state in enumerate(_PROGRESS)}
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class WorkItem:
    mission_id: str
    work_id: str
    intent: str
    baseline_sha: str
    state: WorkState = WorkState.MISSION_CREATED
    risk: str = "R0"
    dependencies: tuple[str, ...] = ()
    acceptance_criteria: tuple[str, ...] = ()
    evidence_requirements: tuple[str, ...] = ()
    attempt_count: int = 0
    lease_id: str | None = None
    failure_fingerprint: str | None = None
    checkpoint: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.mission_id.strip() or not self.work_id.strip() or not self.intent.strip():
            raise WorkloopError("mission_id, work_id, and intent are required")
        if not _SHA_RE.fullmatch(self.baseline_sha):
            raise WorkloopError("baseline_sha must be a 40-character lowercase commit SHA")
        if self.attempt_count < 0:
            raise WorkloopError("attempt_count cannot be negative")
        if self.state == WorkState.LEASED and not self.lease_id:
            raise WorkloopError("LEASED requires lease_id")

    def transition(self, target: WorkState, *, observed_sha: str | None = None, lease_id: str | None = None) -> "WorkItem":
        if self.state in {WorkState.COMPLETED, WorkState.CANCELLED}:
            raise WorkloopError(f"terminal state cannot transition: {self.state.value}")
        if target in {WorkState.BLOCKED, WorkState.QUARANTINED}:
            return WorkItem(**{**self.__dict__, "state": target})
        if target not in _INDEX or self.state not in _INDEX:
            raise WorkloopError("invalid lifecycle state")
        if _INDEX[target] != _INDEX[self.state] + 1:
            raise WorkloopError(f"invalid transition {self.state.value} -> {target.value}")

        mutation_adjacent = target in {
            WorkState.BRANCHED,
            WorkState.DOCUMENTED,
            WorkState.IMPLEMENTED,
            WorkState.DIFF_CAPTURED,
            WorkState.TESTED,
        }
        if observed_sha is not None and observed_sha != self.baseline_sha:
            raise WorkloopError("stale baseline: observed SHA does not match work baseline")
        if mutation_adjacent:
            if observed_sha is None:
                raise WorkloopError("mutation-adjacent state requires an observed baseline SHA")
            active_lease = self.lease_id or lease_id
            if not active_lease:
                raise WorkloopError("mutation-adjacent state requires an active lease")
            if self.lease_id and lease_id is not None and lease_id != self.lease_id:
                raise WorkloopError("lease mismatch")
            if self.lease_id and lease_id is None:
                lease_id = self.lease_id
        next_lease = lease_id if target == WorkState.LEASED else self.lease_id
        return WorkItem(**{**self.__dict__, "state": target, "lease_id": next_lease})

    def failure(self, failure_class: str, evidence_refs: tuple[str, ...]) -> "WorkItem":
        if not failure_class.strip() or not evidence_refs:
            raise WorkloopError("failure requires classification and evidence")
        material = json.dumps(
            {"work_id": self.work_id, "failure_class": failure_class, "evidence_refs": evidence_refs},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        fingerprint = hashlib.sha256(material).hexdigest()
        return WorkItem(**{**self.__dict__, "state": WorkState.QUARANTINED, "failure_fingerprint": fingerprint, "attempt_count": self.attempt_count + 1})


def can_stop(*, required_work: int, recovery_work: int, unresolved_failures: int, unknown: int,
             stale: int, unverified: int, blocked_required: int, uncertified_integrations: int,
             main_verified: bool, final_rescan: bool) -> bool:
    """Return True only when every completion/stop invariant is independently satisfied."""
    counts = (required_work, recovery_work, unresolved_failures, unknown, stale, unverified, blocked_required, uncertified_integrations)
    if any(value != 0 for value in counts):
        return False
    return main_verified and final_rescan


def _strict_bool(value: Any, name: str) -> bool:
    if type(value) is not bool:
        raise WorkloopError(f"{name} must be a boolean")
    return value


def _strict_count(value: Any, name: str) -> int:
    if type(value) is not int or value < 0:
        raise WorkloopError(f"{name} must be a non-negative integer")
    return value


def build_stop_proof(**observations: Any) -> dict[str, Any]:
    """Create a deterministic stop-proof projection; it does not mutate queues.

    This function intentionally accepts only strictly typed observations. It is
    still a projection: callers must supply observations from an independently
    verified scanner before the resulting proof can be treated as authoritative.
    """
    required = {
        "required_work": _strict_count(observations.get("required_work", -1), "required_work"),
        "recovery_work": _strict_count(observations.get("recovery_work", -1), "recovery_work"),
        "unresolved_failures": _strict_count(observations.get("unresolved_failures", -1), "unresolved_failures"),
        "unknown": _strict_count(observations.get("unknown", -1), "unknown"),
        "stale": _strict_count(observations.get("stale", -1), "stale"),
        "unverified": _strict_count(observations.get("unverified", -1), "unverified"),
        "blocked_required": _strict_count(observations.get("blocked_required", -1), "blocked_required"),
        "uncertified_integrations": _strict_count(observations.get("uncertified_integrations", -1), "uncertified_integrations"),
        "main_verified": _strict_bool(observations.get("main_verified", False), "main_verified"),
        "final_rescan": _strict_bool(observations.get("final_rescan", False), "final_rescan"),
    }
    status = "PASS" if can_stop(**required) else "HOLD"
    return {"schema": "research-os-aeos-stop-proof/v1", "status": status, "observations": required, "terminal_state": "CERTIFIED_IDLE" if status == "PASS" else "ACTIVE"}
