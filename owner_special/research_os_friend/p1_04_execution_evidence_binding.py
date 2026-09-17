"""P1-04 bind execution evidence to canonical verification identity.

This is an immutable adapter over existing resource execution and forensic
evidence records. It does not execute verification, mutate AEOS, or grant
authority.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable

from .canonical_identity_federation import CanonicalIdentity, CanonicalIdentityError
from .forensic_evidence_binding import ForensicEvidence, assert_evidence_lineage
from .p1_resource_execution_binding import ResourceExecutionBinding


class P1EvidenceBindingError(CanonicalIdentityError):
    """Raised when execution evidence cannot be bound safely."""


@dataclass(frozen=True)
class ExecutionEvidenceBinding:
    identity: CanonicalIdentity
    resource_binding_hash: str
    evidence_id: str
    provenance_hash: str
    verification_status: str
    evidence_refs: tuple[str, ...]
    verification_fingerprint: str

    @property
    def binding_hash(self) -> str:
        material = {
            "identity": self.identity.fingerprint,
            "resource_binding_hash": self.resource_binding_hash,
            "evidence_id": self.evidence_id,
            "provenance_hash": self.provenance_hash,
            "verification_status": self.verification_status,
            "evidence_refs": self.evidence_refs,
            "verification_fingerprint": self.verification_fingerprint,
        }
        return hashlib.sha256(
            json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


def bind_execution_evidence(
    *,
    identity: CanonicalIdentity,
    resource: ResourceExecutionBinding,
    evidence: ForensicEvidence,
    verification_status: str,
    evidence_refs: Iterable[str] = (),
    verification_fingerprint: str,
) -> ExecutionEvidenceBinding:
    """Create a fail-closed, immutable verification/evidence projection."""
    if resource.resource.canonical != identity:
        raise P1EvidenceBindingError("resource execution is not bound to canonical identity")
    assert_evidence_lineage(evidence, identity)

    if not isinstance(resource.binding_hash, str) or len(resource.binding_hash) != 64:
        raise P1EvidenceBindingError("resource binding hash must be SHA-256")
    if not isinstance(evidence.provenance_hash, str) or len(evidence.provenance_hash) != 64:
        raise P1EvidenceBindingError("evidence provenance hash must be SHA-256")
    if not isinstance(verification_status, str) or not verification_status.strip():
        raise P1EvidenceBindingError("verification_status is required")
    if not isinstance(verification_fingerprint, str) or len(verification_fingerprint) != 64:
        raise P1EvidenceBindingError("verification_fingerprint must be SHA-256")

    refs = tuple(evidence_refs)
    combined = tuple(dict.fromkeys((*evidence.source_refs, *refs)))
    if any(not isinstance(ref, str) or not ref.strip() for ref in combined):
        raise P1EvidenceBindingError("evidence_refs must contain non-empty strings")

    return ExecutionEvidenceBinding(
        identity=identity,
        resource_binding_hash=resource.binding_hash,
        evidence_id=evidence.evidence_id,
        provenance_hash=evidence.provenance_hash,
        verification_status=verification_status.strip(),
        evidence_refs=tuple(ref.strip() for ref in combined),
        verification_fingerprint=verification_fingerprint,
    )


def assert_execution_evidence_lineage(
    binding: ExecutionEvidenceBinding,
    identity: CanonicalIdentity,
) -> None:
    """Fail closed if a verification projection crosses canonical lineage."""
    if binding.identity != identity:
        raise P1EvidenceBindingError("verification evidence lineage does not match canonical identity")
