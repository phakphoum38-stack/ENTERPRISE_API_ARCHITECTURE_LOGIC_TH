"""P0-9 distributed/concurrent coordination boundary.

This module models bounded ownership/fencing metadata for concurrent fleet
projects. It does not schedule, enqueue, execute, lease through infrastructure,
or mutate any worker. Existing Scheduler/AEOS/queue/lease adapters remain
authoritative.

The module provides immutable coordination records that an adapter may validate
before applying an already-authorized operation.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib

from .canonical_identity_federation import CanonicalIdentity, CanonicalIdentityError
from .project_fleet import ProjectFleet


class DistributedCoordinationError(CanonicalIdentityError):
    """Raised when distributed coordination invariants are violated."""


@dataclass(frozen=True)
class CoordinationClaim:
    project_id: str
    identity: CanonicalIdentity
    owner_id: str
    epoch: int
    claim_id: str
    active: bool = True

    def __post_init__(self) -> None:
        if not self.project_id.strip():
            raise DistributedCoordinationError("project_id is required")
        if not self.owner_id.strip():
            raise DistributedCoordinationError("owner_id is required")
        if not self.claim_id.strip():
            raise DistributedCoordinationError("claim_id is required")
        if self.epoch < 1:
            raise DistributedCoordinationError("epoch must be >= 1")

    def fingerprint(self) -> str:
        material = (
            self.project_id,
            self.identity.fingerprint(),
            self.owner_id,
            str(self.epoch),
            self.claim_id,
            str(self.active),
        )
        return hashlib.sha256("|".join(material).encode()).hexdigest()

    def fenced(self, *, epoch: int) -> bool:
        """Return True only when this claim is current and active."""
        return self.active and self.epoch == epoch


@dataclass(frozen=True)
class ConcurrentProject:
    project_id: str
    identity: CanonicalIdentity
    max_parallel_units: int = 1
    active_units: int = 0

    def __post_init__(self) -> None:
        if self.max_parallel_units < 1:
            raise DistributedCoordinationError("max_parallel_units must be >= 1")
        if self.active_units < 0 or self.active_units > self.max_parallel_units:
            raise DistributedCoordinationError("active_units exceeds concurrency bound")

    def acquire_slot(self) -> "ConcurrentProject":
        """Record a bounded slot reservation; no work is executed."""
        if self.active_units >= self.max_parallel_units:
            raise DistributedCoordinationError("project concurrency bound reached")
        return replace(self, active_units=self.active_units + 1)

    def release_slot(self) -> "ConcurrentProject":
        if self.active_units < 1:
            raise DistributedCoordinationError("no active concurrency slot")
        return replace(self, active_units=self.active_units - 1)


def validate_fleet_membership(fleet: ProjectFleet, project: ConcurrentProject) -> None:
    registered = fleet.get(project.project_id)
    if registered.identity != project.identity:
        raise DistributedCoordinationError("fleet/project canonical identity mismatch")


def validate_claim(
    *,
    fleet: ProjectFleet,
    claim: CoordinationClaim,
    expected_epoch: int,
) -> None:
    validate_fleet_membership(
        fleet,
        ConcurrentProject(claim.project_id, claim.identity),
    )
    if not claim.fenced(epoch=expected_epoch):
        raise DistributedCoordinationError("stale or inactive coordination claim")


def next_epoch(claim: CoordinationClaim) -> CoordinationClaim:
    """Return a new fenced epoch without revoking infrastructure ownership itself."""
    return replace(claim, epoch=claim.epoch + 1, active=True)


def deactivate(claim: CoordinationClaim) -> CoordinationClaim:
    return replace(claim, active=False)
