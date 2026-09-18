"""P1-12 cross-shard correlation projection.

Binds the 10^10 logical-project address to the existing canonical identity and
functional integration trace without creating a new execution or governance
plane. This is a pure validation/projection boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .canonical_identity_federation import CanonicalIdentity, CanonicalIdentityError
from .p1_functional_integration import P1FunctionalIntegrationTrace
from .ten_billion_federation import LogicalProjectAddress, TenBillionFederationProjection


class CrossShardCorrelationError(CanonicalIdentityError):
    """Raised when logical-project correlation cannot be proven."""


@dataclass(frozen=True)
class CrossShardCorrelation:
    project_id: str
    namespace: str
    partition_id: int
    slot: int
    identity_fingerprint: str
    integration_fingerprint: str
    correlation_fingerprint: str


def correlate_cross_shard(
    *,
    federation: TenBillionFederationProjection,
    address: LogicalProjectAddress,
    identity: CanonicalIdentity,
    integration: P1FunctionalIntegrationTrace,
) -> CrossShardCorrelation:
    if not address.project_id.strip():
        raise CrossShardCorrelationError("project correlation requires project_id")
    if address.namespace != identity.mission_id:
        raise CrossShardCorrelationError("logical namespace does not match mission")
    if integration.identity_fingerprint != identity.fingerprint():
        raise CrossShardCorrelationError("integration identity fingerprint mismatch")
    if integration.work_id != identity.work_id:
        raise CrossShardCorrelationError("integration work lineage mismatch")
    if integration.mission_id != identity.mission_id:
        raise CrossShardCorrelationError("integration mission lineage mismatch")
    expected = federation.address(namespace=identity.mission_id, project_id=address.project_id)
    if expected != address:
        raise CrossShardCorrelationError("address is not deterministically derived")
    material = "|".join(
        (
            address.fingerprint(),
            identity.fingerprint(),
            integration.integration_fingerprint,
        )
    )
    return CrossShardCorrelation(
        project_id=address.project_id,
        namespace=address.namespace,
        partition_id=address.partition_id,
        slot=address.slot,
        identity_fingerprint=identity.fingerprint(),
        integration_fingerprint=integration.integration_fingerprint,
        correlation_fingerprint=hashlib.sha256(material.encode("utf-8")).hexdigest(),
    )
