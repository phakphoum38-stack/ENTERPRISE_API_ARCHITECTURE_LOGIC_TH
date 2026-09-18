"""P1-199 bounded federation evidence projection."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json
from .canonical_identity_federation import CanonicalIdentity,CanonicalIdentityError
from .p1_04_execution_evidence_binding import ExecutionEvidenceBinding
class P1199Error(CanonicalIdentityError): pass
@dataclass(frozen=True)
class P1199Projection:
    identity: CanonicalIdentity
    evidence_ids: tuple[str,...]
    binding_hashes: tuple[str,...]
    fingerprint: str
    @property
    def projection_hash(self)->str:
        return hashlib.sha256(json.dumps({"stage":199,"identity":self.identity.fingerprint(),"evidence_ids":self.evidence_ids,"binding_hashes":self.binding_hashes,"fingerprint":self.fingerprint},sort_keys=True,separators=(",",":")).encode()).hexdigest()
def project_p1_199(*,identity:CanonicalIdentity,bindings:list[ExecutionEvidenceBinding],fingerprint:str)->P1199Projection:
    if len(fingerprint)!=64: raise P1199Error("fingerprint must be SHA-256")
    if not bindings: raise P1199Error("evidence binding is required")
    for x in bindings:
        if x.identity!=identity: raise P1199Error("evidence crosses canonical lineage")
        if len(x.binding_hash)!=64: raise P1199Error("binding hash must be SHA-256")
    return P1199Projection(identity,tuple(dict.fromkeys(x.evidence_id for x in bindings)),tuple(dict.fromkeys(x.binding_hash for x in bindings)),fingerprint)
