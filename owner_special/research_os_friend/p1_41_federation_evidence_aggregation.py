"""P1-41 federation evidence aggregation boundary.

Composes existing P1-15 correlation and P1-16..40 projections into one
immutable aggregation boundary. No new execution, storage, scheduler, queue,
worker, authority, merge, or CI behavior.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from .canonical_identity_federation import CanonicalIdentity, CanonicalIdentityError
from .p1_04_execution_evidence_binding import ExecutionEvidenceBinding
from .p1_15_cross_partition_evidence_correlation import CrossPartitionEvidenceCorrelation

class P1_41Error(CanonicalIdentityError):
    """Raised when federation aggregation cannot be proven."""

@dataclass(frozen=True)
class FederationEvidenceAggregation:
    identity: CanonicalIdentity
    correlation_hash: str
    projection_hashes: tuple[str, ...]
    aggregation_fingerprint: str
    @property
    def aggregation_hash(self)->str:
        material={"identity":self.identity.fingerprint(),"correlation_hash":self.correlation_hash,"projection_hashes":self.projection_hashes,"aggregation_fingerprint":self.aggregation_fingerprint}
        return hashlib.sha256(json.dumps(material,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def aggregate_federation_evidence(
    *, identity: CanonicalIdentity,
    correlation: CrossPartitionEvidenceCorrelation,
    projections: tuple[object,...]=(),
    aggregation_fingerprint: str,
)->FederationEvidenceAggregation:
    if correlation.identity != identity:
        raise P1_41Error("correlation crosses canonical lineage")
    if not isinstance(aggregation_fingerprint,str) or len(aggregation_fingerprint)!=64:
        raise P1_41Error("aggregation_fingerprint must be SHA-256")
    hashes=[]
    for projection in projections:
        h=getattr(projection,"projection_hash",None)
        if not isinstance(h,str) or len(h)!=64:
            raise P1_41Error("projection hash must be SHA-256")
        if getattr(projection,"identity",identity) != identity:
            raise P1_41Error("projection crosses canonical lineage")
        hashes.append(h)
    return FederationEvidenceAggregation(identity,correlation.correlation_hash,tuple(dict.fromkeys(hashes)),aggregation_fingerprint)

def assert_federation_evidence_aggregation(
    aggregation:FederationEvidenceAggregation, identity:CanonicalIdentity
)->None:
    if aggregation.identity != identity:
        raise P1_41Error("aggregation lineage mismatch")
