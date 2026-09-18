"""P1-34 evidence retention boundary projection.

Pure validation/projection over existing canonical evidence bindings.
No new execution, storage, scheduler, queue, worker, authority, merge,
or CI behavior.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json
from .canonical_identity_federation import CanonicalIdentity,CanonicalIdentityError
from .p1_04_execution_evidence_binding import ExecutionEvidenceBinding
class P134Error(CanonicalIdentityError): pass
@dataclass(frozen=True)
class P134Projection:
    identity: CanonicalIdentity
    evidence_ids: tuple[str,...]
    binding_hashes: tuple[str,...]
    fingerprint: str
    @property
    def projection_hash(self)->str:
        m={"stage":34,"identity":self.identity.fingerprint(),"evidence_ids":self.evidence_ids,"binding_hashes":self.binding_hashes,"fingerprint":self.fingerprint}
        return hashlib.sha256(json.dumps(m,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def project_p1_34(*,identity:CanonicalIdentity,bindings:list[ExecutionEvidenceBinding],fingerprint:str)->P134Projection:
    if len(fingerprint)!=64: raise P134Error("fingerprint must be SHA-256")
    if not bindings: raise P134Error("evidence binding is required")
    for x in bindings:
        if x.identity!=identity: raise P134Error("evidence crosses canonical lineage")
        if len(x.binding_hash)!=64: raise P134Error("binding hash must be SHA-256")
        if not x.evidence_id.strip(): raise P134Error("evidence_id is required")
    return P134Projection(identity,tuple(dict.fromkeys(x.evidence_id for x in bindings)),tuple(dict.fromkeys(x.binding_hash for x in bindings)),fingerprint)
def assert_p1_34_lineage(projection:P134Projection,identity:CanonicalIdentity)->None:
    if projection.identity!=identity: raise P134Error("projection lineage mismatch")
