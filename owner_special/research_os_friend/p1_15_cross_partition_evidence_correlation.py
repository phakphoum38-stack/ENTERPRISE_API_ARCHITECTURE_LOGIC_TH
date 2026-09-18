"""P1-15 cross-partition evidence correlation projection.

Correlates evidence projections from multiple logical federation partitions
without creating a new evidence store, execution plane, scheduler, worker,
authority boundary, or merge path.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable

from .canonical_identity_federation import CanonicalIdentity, CanonicalIdentityError
from .p1_04_execution_evidence_binding import ExecutionEvidenceBinding
from .p1_14_project_namespace_isolation import (
    ProjectNamespaceIsolation,
    assert_namespace_isolation,
)


class CrossPartitionEvidenceCorrelationError(CanonicalIdentityError):
    """Raised when cross-partition evidence correlation cannot be proven."""


@dataclass(frozen=True)
class CrossPartitionEvidenceCorrelation:
    identity: CanonicalIdentity
    project_id: str
    partition_ids: tuple[int, ...]
    evidence_ids: tuple[str, ...]
    binding_hashes: tuple[str, ...]
    correlation_fingerprint: str

    @property
    def correlation_hash(self) -> str:
        material = {
            "identity": self.identity.fingerprint(),
            "project_id": self.project_id,
            "partition_ids": self.partition_ids,
            "evidence_ids": self.evidence_ids,
            "binding_hashes": self.binding_hashes,
            "correlation_fingerprint": self.correlation_fingerprint,
        }
        return hashlib.sha256(
            json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


def correlate_cross_partition_evidence(
    *,
    identity: CanonicalIdentity,
    isolation: ProjectNamespaceIsolation,
    bindings: Iterable[ExecutionEvidenceBinding],
    correlation_fingerprint: str,
) -> CrossPartitionEvidenceCorrelation:
    """Correlate existing evidence bindings across logical partitions."""
    assert_namespace_isolation(isolation, identity)

    if isolation.project_id.strip() == "":
        raise CrossPartitionEvidenceCorrelationError("project_id is required")
    if not isinstance(correlation_fingerprint, str) or len(correlation_fingerprint) != 64:
        raise CrossPartitionEvidenceCorrelationError(
            "correlation_fingerprint must be SHA-256"
        )

    items = tuple(bindings)
    if not items:
        raise CrossPartitionEvidenceCorrelationError("at least one evidence binding is required")

    for binding in items:
        if binding.identity != identity:
            raise CrossPartitionEvidenceCorrelationError(
                "evidence binding crosses canonical lineage"
            )
        if not isinstance(binding.binding_hash, str) or len(binding.binding_hash) != 64:
            raise CrossPartitionEvidenceCorrelationError(
                "evidence binding hash must be SHA-256"
            )
        if not binding.evidence_id.strip():
            raise CrossPartitionEvidenceCorrelationError("evidence_id is required")

    # Partition IDs are routing metadata only; they never redefine identity.
    partition_ids = tuple(sorted({isolation.partition_id}))
    evidence_ids = tuple(dict.fromkeys(binding.evidence_id for binding in items))
    binding_hashes = tuple(dict.fromkeys(binding.binding_hash for binding in items))

    return CrossPartitionEvidenceCorrelation(
        identity=identity,
        project_id=isolation.project_id,
        partition_ids=partition_ids,
        evidence_ids=evidence_ids,
        binding_hashes=binding_hashes,
        correlation_fingerprint=correlation_fingerprint,
    )


def assert_cross_partition_evidence_correlation(
    correlation: CrossPartitionEvidenceCorrelation,
    identity: CanonicalIdentity,
) -> None:
    """Fail closed if correlation crosses canonical identity lineage."""
    if correlation.identity != identity:
        raise CrossPartitionEvidenceCorrelationError(
            "correlation lineage does not match canonical identity"
        )
    if correlation.identity.fingerprint() != identity.fingerprint():
        raise CrossPartitionEvidenceCorrelationError(
            "correlation identity fingerprint mismatch"
        )
