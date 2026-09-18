"""P1-19 Evidence Completeness Projection.

Pure projection/validation over existing Research OS evidence and canonical
identity. No new execution, scheduler, queue, worker, authority, merge,
storage, or CI behavior.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
from typing import Iterable

from .canonical_identity_federation import CanonicalIdentity, CanonicalIdentityError
from .p1_04_execution_evidence_binding import ExecutionEvidenceBinding


class P119Error(CanonicalIdentityError):
    """Raised when the P1-19 contract cannot be proven."""


@dataclass(frozen=True)
class P119Projection:
    identity: CanonicalIdentity
    evidence_ids: tuple[str, ...]
    binding_hashes: tuple[str, ...]
    fingerprint: str

    @property
    def projection_hash(self) -> str:
        material = {
            "identity": self.identity.fingerprint(),
            "evidence_ids": self.evidence_ids,
            "binding_hashes": self.binding_hashes,
            "fingerprint": self.fingerprint,
        }
        return hashlib.sha256(
            json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


def project_p1_19(
    *, identity: CanonicalIdentity,
    bindings: Iterable[ExecutionEvidenceBinding],
    fingerprint: str,
) -> P119Projection:
    """Checks that correlated evidence has the declared required references and lineage."""
    if not isinstance(fingerprint, str) or len(fingerprint) != 64:
        raise P119Error("fingerprint must be SHA-256")
    items = tuple(bindings)
    if not items:
        raise P119Error("at least one evidence binding is required")
    for item in items:
        if item.identity != identity:
            raise P119Error("evidence crosses canonical lineage")
        if not isinstance(item.binding_hash, str) or len(item.binding_hash) != 64:
            raise P119Error("binding hash must be SHA-256")
        if not isinstance(item.evidence_id, str) or not item.evidence_id.strip():
            raise P119Error("evidence_id is required")
    return P119Projection(
        identity=identity,
        evidence_ids=tuple(dict.fromkeys(x.evidence_id for x in items)),
        binding_hashes=tuple(dict.fromkeys(x.binding_hash for x in items)),
        fingerprint=fingerprint,
    )


def assert_p1_19_lineage(
    projection: P119Projection, identity: CanonicalIdentity
) -> None:
    if projection.identity != identity:
        raise P119Error("projection lineage mismatch")
