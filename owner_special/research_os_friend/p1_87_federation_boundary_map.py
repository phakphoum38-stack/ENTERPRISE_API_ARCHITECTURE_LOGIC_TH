"""P1-87 federation_boundary_map projection.
Pure validation over existing canonical federation evidence.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json
from .canonical_identity_federation import CanonicalIdentity,CanonicalIdentityError
from .p1_04_execution_evidence_binding import ExecutionEvidenceBinding
class P187Error(CanonicalIdentityError): pass
@dataclass(frozen=True)
class P187Projection:
    identity: CanonicalIdentity
    evidence_ids: tuple[str,...]
    binding_hashes: tuple[str,...]
    fingerprint: str
    @property
    def projection_hash(self)->str:
        return hashlib.sha256(json.dumps({"stage":87,"identity":self.identity.fingerprint(),"evidence_ids":self.evidence_ids,"binding_hashes":self.binding_hashes,"fingerprint":self.fingerprint},sort_keys=True,separators=(",",":")).encode()).hexdigest()
def project_p1_87(*,identity:CanonicalIdentity,bindings:list[ExecutionEvidenceBinding],fingerprint:str)->P187Projection:
    if len(fingerprint)!=64: raise P187Error("fingerprint must be SHA-256")
    if not bindings: raise P187Error("evidence binding is required")
    for x in bindings:
        if x.identity!=identity: raise P187Error("evidence crosses canonical lineage")
        if len(x.binding_hash)!=64: raise P187Error("binding hash must be SHA-256")
        if not x.evidence_id.strip(): raise P187Error("evidence_id is required")
    return P187Projection(identity,tuple(dict.fromkeys(x.evidence_id for x in bindings)),tuple(dict.fromkeys(x.binding_hash for x in bindings)),fingerprint)
