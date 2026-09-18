"""P1-16..40 bounded federation evidence projection registry.

These numbered projections are intentionally composed in one module: they
remain pure validation/projection boundaries over existing evidence bindings.
No new storage, scheduler, queue, worker, execution engine, authority, merge,
or CI behavior is introduced.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from typing import Iterable
from .canonical_identity_federation import CanonicalIdentity, CanonicalIdentityError
from .p1_04_execution_evidence_binding import ExecutionEvidenceBinding

class P1FederationEvidenceError(CanonicalIdentityError): pass

@dataclass(frozen=True)
class FederationEvidenceProjection:
    stage: int
    identity: CanonicalIdentity
    evidence_ids: tuple[str,...]
    binding_hashes: tuple[str,...]
    fingerprint: str
    @property
    def projection_hash(self)->str:
        m={"stage":self.stage,"identity":self.identity.fingerprint(),"evidence_ids":self.evidence_ids,"binding_hashes":self.binding_hashes,"fingerprint":self.fingerprint}
        return hashlib.sha256(json.dumps(m,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def project_federation_evidence(stage:int, *, identity:CanonicalIdentity, bindings:Iterable[ExecutionEvidenceBinding], fingerprint:str)->FederationEvidenceProjection:
    if stage<16 or stage>40: raise P1FederationEvidenceError("stage must be P1-16 through P1-40")
    if not isinstance(fingerprint,str) or len(fingerprint)!=64: raise P1FederationEvidenceError("fingerprint must be SHA-256")
    items=tuple(bindings)
    if not items: raise P1FederationEvidenceError("evidence binding is required")
    for x in items:
        if x.identity!=identity: raise P1FederationEvidenceError("evidence crosses canonical lineage")
        if len(x.binding_hash)!=64: raise P1FederationEvidenceError("binding hash must be SHA-256")
        if not x.evidence_id.strip(): raise P1FederationEvidenceError("evidence_id is required")
    return FederationEvidenceProjection(stage,identity,tuple(dict.fromkeys(x.evidence_id for x in items)),tuple(dict.fromkeys(x.binding_hash for x in items)),fingerprint)

def assert_federation_evidence_lineage(p:FederationEvidenceProjection, identity:CanonicalIdentity)->None:
    if p.identity!=identity: raise P1FederationEvidenceError("projection lineage mismatch")
