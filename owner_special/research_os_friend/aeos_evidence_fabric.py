"""AEOS evidence-fabric integrity boundary.

The fabric canonicalizes evidence references and immutable roots. It does not
claim that evidence is true, fresh, independent, or authoritative; those are
separate verification concerns.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable, Mapping


class EvidenceFabricError(ValueError):
    """Raised when evidence cannot be bound into the fabric."""


_SHA256 = 64


def _sha(value: str) -> None:
    if not isinstance(value, str) or len(value) != _SHA256:
        raise EvidenceFabricError("invalid SHA256 root")
    if any(char not in "0123456789abcdef" for char in value):
        raise EvidenceFabricError("invalid SHA256 root")


def _canonical_refs(refs: Iterable[str]) -> tuple[str, ...]:
    result = tuple(refs)
    if not result:
        raise EvidenceFabricError("evidence_refs required")
    if any(not isinstance(ref, str) or not ref for ref in result):
        raise EvidenceFabricError("invalid evidence reference")
    if len(set(result)) != len(result):
        raise EvidenceFabricError("duplicate evidence reference")
    return tuple(sorted(result))


def evidence_root(*, evidence_refs: Iterable[str]) -> str:
    """Return the deterministic root for a canonical evidence-reference set."""
    refs = _canonical_refs(evidence_refs)
    payload = json.dumps(refs, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class EvidenceBundle:
    bundle_id: str
    baseline_sha: str
    contract_sha256: str
    policy_sha256: str
    evidence_refs: tuple[str, ...]
    evidence_root: str
    source_fingerprints: Mapping[str, str]

    def __post_init__(self) -> None:
        if not isinstance(self.bundle_id, str) or not self.bundle_id:
            raise EvidenceFabricError("bundle_id required")
        if not isinstance(self.baseline_sha, str) or len(self.baseline_sha) != 40:
            raise EvidenceFabricError("invalid baseline SHA")
        if any(char not in "0123456789abcdef" for char in self.baseline_sha):
            raise EvidenceFabricError("invalid baseline SHA")
        _sha(self.contract_sha256)
        _sha(self.policy_sha256)
        refs = _canonical_refs(self.evidence_refs)
        if refs != self.evidence_refs:
            raise EvidenceFabricError("evidence_refs must be canonical")
        _sha(self.evidence_root)
        if self.evidence_root != evidence_root(evidence_refs=refs):
            raise EvidenceFabricError("evidence root mismatch")
        if not isinstance(self.source_fingerprints, Mapping):
            raise EvidenceFabricError("source_fingerprints required")
        if set(self.source_fingerprints) != set(refs):
            raise EvidenceFabricError("source fingerprint coverage mismatch")
        for fingerprint in self.source_fingerprints.values():
            _sha(fingerprint)


def bind_evidence_bundle(
    *,
    bundle_id: str,
    baseline_sha: str,
    contract_sha256: str,
    policy_sha256: str,
    evidence_refs: Iterable[str],
    source_fingerprints: Mapping[str, str],
) -> EvidenceBundle:
    """Bind evidence metadata without converting it into authority or truth."""
    refs = _canonical_refs(evidence_refs)
    if not isinstance(baseline_sha, str) or len(baseline_sha) != 40 or any(c not in "0123456789abcdef" for c in baseline_sha):
        raise EvidenceFabricError("invalid baseline SHA")
    _sha(contract_sha256)
    _sha(policy_sha256)
    if not isinstance(source_fingerprints, Mapping) or set(source_fingerprints) != set(refs):
        raise EvidenceFabricError("source fingerprint coverage mismatch")
    for fingerprint in source_fingerprints.values():
        _sha(fingerprint)
    return EvidenceBundle(
        bundle_id=bundle_id,
        baseline_sha=baseline_sha,
        contract_sha256=contract_sha256,
        policy_sha256=policy_sha256,
        evidence_refs=refs,
        evidence_root=evidence_root(evidence_refs=refs),
        source_fingerprints=dict(source_fingerprints),
    )
