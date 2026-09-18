"""10^10 logical-project federation boundary.

This is a deterministic addressing/projection layer, not a new execution plane.
It models up to 10,000,000,000 logical project identities without materializing
them in the bounded ProjectFleet registry.

The existing ProjectFleet remains the bounded operational view. Existing AEOS,
Scheduler, queues, workers, verification, evidence, and governance boundaries
remain authoritative.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .canonical_identity_federation import CanonicalIdentity, CanonicalIdentityError
from .project_fleet import ProjectFleet
from .distributed_coordination import CoordinationClaim


class TenBillionFederationError(CanonicalIdentityError):
    """Raised when a 10^10 federation invariant is violated."""


LOGICAL_PROJECT_CAPACITY = 10_000_000_000
DEFAULT_PARTITION_COUNT = 1_000_000


@dataclass(frozen=True)
class LogicalProjectAddress:
    """Deterministic address for one logical project."""

    namespace: str
    project_id: str
    partition_id: int
    slot: int

    def __post_init__(self) -> None:
        if not self.namespace.strip():
            raise TenBillionFederationError("namespace is required")
        if not self.project_id.strip():
            raise TenBillionFederationError("project_id is required")
        if self.partition_id < 0:
            raise TenBillionFederationError("partition_id must be >= 0")
        if self.slot < 0:
            raise TenBillionFederationError("slot must be >= 0")

    def key(self) -> str:
        return f"{self.namespace}:{self.project_id}"

    def fingerprint(self) -> str:
        return hashlib.sha256(
            "|".join(
                (self.namespace, self.project_id, str(self.partition_id), str(self.slot))
            ).encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True)
class FederationPartition:
    """Declarative partition descriptor; it owns no execution resources."""

    partition_id: int
    capacity: int
    logical_count: int = 0

    def __post_init__(self) -> None:
        if self.partition_id < 0:
            raise TenBillionFederationError("partition_id must be >= 0")
        if self.capacity < 1:
            raise TenBillionFederationError("partition capacity must be >= 1")
        if self.logical_count < 0 or self.logical_count > self.capacity:
            raise TenBillionFederationError("logical_count exceeds partition capacity")


@dataclass(frozen=True)
class TenBillionFederationProjection:
    """Immutable federation projection over existing execution/governance planes."""

    logical_capacity: int = LOGICAL_PROJECT_CAPACITY
    partition_count: int = DEFAULT_PARTITION_COUNT
    operational_view_capacity: int = 100

    def __post_init__(self) -> None:
        if self.logical_capacity != LOGICAL_PROJECT_CAPACITY:
            raise TenBillionFederationError("logical capacity must remain 10^10")
        if self.partition_count < 1:
            raise TenBillionFederationError("partition_count must be >= 1")
        if self.logical_capacity % self.partition_count:
            raise TenBillionFederationError(
                "logical capacity must divide evenly across partitions"
            )
        if self.operational_view_capacity != 100:
            raise TenBillionFederationError("operational view must remain bounded at 100")

    @property
    def partition_capacity(self) -> int:
        return self.logical_capacity // self.partition_count

    def address(self, *, namespace: str, project_id: str) -> LogicalProjectAddress:
        material = f"{namespace}\0{project_id}".encode("utf-8")
        digest = hashlib.sha256(material).digest()
        ordinal = int.from_bytes(digest[:8], "big") % self.logical_capacity
        partition_id = ordinal // self.partition_capacity
        slot = ordinal % self.partition_capacity
        return LogicalProjectAddress(namespace, project_id, partition_id, slot)

    def validate_operational_view(self, fleet: ProjectFleet) -> None:
        if fleet.capacity != self.operational_view_capacity:
            raise TenBillionFederationError(
                "operational ProjectFleet capacity no longer matches bounded view"
            )
        for project in fleet.projects:
            expected = self.address(
                namespace=project.identity.mission_id,
                project_id=project.project_id,
            )
            if expected.project_id != project.project_id:
                raise TenBillionFederationError("fleet project addressing mismatch")

    def correlation_key(
        self,
        *,
        address: LogicalProjectAddress,
        identity: CanonicalIdentity,
    ) -> str:
        if identity.mission_id != address.namespace:
            raise TenBillionFederationError("identity namespace mismatch")
        material = "|".join(
            (
                address.fingerprint(),
                identity.fingerprint(),
                str(address.partition_id),
            )
        )
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    def validate_claim(
        self,
        *,
        address: LogicalProjectAddress,
        identity: CanonicalIdentity,
        claim: CoordinationClaim,
        expected_epoch: int,
    ) -> None:
        if claim.project_id != address.project_id:
            raise TenBillionFederationError("claim project mismatch")
        if claim.identity != identity:
            raise TenBillionFederationError("claim identity mismatch")
        if not claim.fenced(epoch=expected_epoch):
            raise TenBillionFederationError("stale or inactive claim")


def build_ten_billion_projection(
    *,
    partition_count: int = DEFAULT_PARTITION_COUNT,
) -> TenBillionFederationProjection:
    return TenBillionFederationProjection(partition_count=partition_count)
