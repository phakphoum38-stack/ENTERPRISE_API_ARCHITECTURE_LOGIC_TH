"""P1-39 evidence handoff projection.

Pure validation/projection over existing canonical evidence bindings.
No new execution, storage, scheduler, queue, worker, authority, merge,
or CI behavior.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json
from .canonical_identity_federation import CanonicalIdentity,CanonicalIdentityError
from .p1_04_execution_evidence_binding import ExecutionEvidenceBinding
class P139Error(CanonicalIdentityError): pass
@dataclass(frozen=True)
class P139Projection:
    identity: CanonicalIdentity
    evidence_ids: tuple[str,...]
    binding_hashes: tuple[str,...]
    fingerprint: str
    @property
    def projection_hash(self)->str:
        m={"stage":39,"identity":self.identity.fingerprint(),"evidence_ids":self.evidence_ids,"binding_hashes":self.binding_hashes,"fingerprint":self.fingerprint}
        return hashlib.sha256(json.dumps(m,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def project_p1_39(*,identity:CanonicalIdentity,bindings:list[ExecutionEvidenceBinding],fingerprint:str)->P139Projection:
    if len(fingerprint)!=64: raise P139Error("fingerprint must be SHA-256")
    if not bindings: raise P139Error("evidence binding is required")
    for x in bindings:
        if x.identity!=identity: raise P139Error("evidence crosses canonical lineage")
        if len(x.binding_hash)!=64: raise P139Error("binding hash must be SHA-256")
        if not x.evidence_id.strip(): raise P139Error("evidence_id is required")
    return P139Projection(identity,tuple(dict.fromkeys(x.evidence_id for x in bindings)),tuple(dict.fromkeys(x.binding_hash for x in bindings)),fingerprint)
def assert_p1_39_lineage(projection:P139Projection,identity:CanonicalIdentity)->None:
    if projection.identity!=identity: raise P139Error("projection lineage mismatch")
