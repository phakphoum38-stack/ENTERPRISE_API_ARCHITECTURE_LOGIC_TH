"""P1-13 shard-independent lineage projection.

Provides a deterministic lineage record that remains identical in meaning
regardless of the logical partition selected for a project. This is a pure
projection/validation boundary over existing Canonical Identity and
10^10 federation addressing.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .canonical_identity_federation import CanonicalIdentity, CanonicalIdentityError
from .ten_billion_federation import LogicalProjectAddress, TenBillionFederationProjection


class ShardIndependentLineageError(CanonicalIdentityError):
    """Raised when shard-independent lineage cannot be proven."""


@dataclass(frozen=True)
class ShardIndependentLineage:
    mission_id: str
    work_id: str
    baseline_sha: str
    project_id: str
    namespace: str
    partition_id: int
    slot: int
    identity_fingerprint: str
    lineage_fingerprint: str


def project_shard_independent_lineage(
    *,
    federation: TenBillionFederationProjection,
    address: LogicalProjectAddress,
    identity: CanonicalIdentity,
) -> ShardIndependentLineage:
    if address.namespace != identity.mission_id:
        raise ShardIndependentLineageError("address namespace mismatch")
    if not address.project_id.strip():
        raise ShardIndependentLineageError("project_id is required")
    expected = federation.address(
        namespace=identity.mission_id,
        project_id=address.project_id,
    )
    if expected != address:
        raise ShardIndependentLineageError("address is not deterministically derived")

    # Partition is routing metadata; canonical lineage remains mission/work/baseline.
    material = "|".join(
        (
            identity.mission_id,
            identity.work_id,
            identity.baseline_sha,
            address.project_id,
        )
    )
    return ShardIndependentLineage(
        mission_id=identity.mission_id,
        work_id=identity.work_id,
        baseline_sha=identity.baseline_sha,
        project_id=address.project_id,
        namespace=address.namespace,
        partition_id=address.partition_id,
        slot=address.slot,
        identity_fingerprint=identity.fingerprint(),
        lineage_fingerprint=hashlib.sha256(material.encode("utf-8")).hexdigest(),
    )


def assert_shard_independent_lineage(
    lineage: ShardIndependentLineage,
    identity: CanonicalIdentity,
) -> None:
    if lineage.mission_id != identity.mission_id:
        raise ShardIndependentLineageError("mission lineage mismatch")
    if lineage.work_id != identity.work_id:
        raise ShardIndependentLineageError("work lineage mismatch")
    if lineage.baseline_sha != identity.baseline_sha:
        raise ShardIndependentLineageError("baseline lineage mismatch")
    if lineage.identity_fingerprint != identity.fingerprint():
        raise ShardIndependentLineageError("identity fingerprint mismatch")
