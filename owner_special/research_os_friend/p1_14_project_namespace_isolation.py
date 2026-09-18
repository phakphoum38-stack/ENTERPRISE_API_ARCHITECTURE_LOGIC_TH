"""P1-14 project namespace isolation projection.

Validates that logical project addressing is isolated by namespace while
preserving the existing canonical mission/work/baseline lineage. Pure
projection only; no execution or authority behavior is introduced.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .canonical_identity_federation import CanonicalIdentity, CanonicalIdentityError
from .ten_billion_federation import TenBillionFederationProjection, LogicalProjectAddress


class ProjectNamespaceIsolationError(CanonicalIdentityError):
    """Raised when project namespace isolation cannot be proven."""


@dataclass(frozen=True)
class ProjectNamespaceIsolation:
    namespace: str
    project_id: str
    partition_id: int
    slot: int
    identity_fingerprint: str
    namespace_fingerprint: str


def isolate_project_namespace(
    *,
    federation: TenBillionFederationProjection,
    identity: CanonicalIdentity,
    address: LogicalProjectAddress,
) -> ProjectNamespaceIsolation:
    if not identity.mission_id.strip():
        raise ProjectNamespaceIsolationError("mission namespace is required")
    if address.namespace != identity.mission_id:
        raise ProjectNamespaceIsolationError("project namespace mismatch")
    expected = federation.address(
        namespace=identity.mission_id,
        project_id=address.project_id,
    )
    if expected != address:
        raise ProjectNamespaceIsolationError("project address is not deterministic")
    material = "|".join((identity.mission_id, address.project_id, identity.fingerprint()))
    return ProjectNamespaceIsolation(
        namespace=address.namespace,
        project_id=address.project_id,
        partition_id=address.partition_id,
        slot=address.slot,
        identity_fingerprint=identity.fingerprint(),
        namespace_fingerprint=hashlib.sha256(material.encode("utf-8")).hexdigest(),
    )


def assert_namespace_isolation(
    isolation: ProjectNamespaceIsolation,
    identity: CanonicalIdentity,
) -> None:
    if isolation.namespace != identity.mission_id:
        raise ProjectNamespaceIsolationError("namespace lineage mismatch")
    if isolation.identity_fingerprint != identity.fingerprint():
        raise ProjectNamespaceIsolationError("identity fingerprint mismatch")
