"""P0-5 bridge: forensic proof into canonical evidence/provenance.

This module records a deterministic, fail-closed evidence reference for a
canonical work lineage. It does not claim subject truth, grant authority, or
execute forensic probes.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from typing import Iterable
from .canonical_identity_federation import CanonicalIdentity, CanonicalIdentityError

class ForensicEvidenceError(CanonicalIdentityError):
    """Raised when forensic evidence cannot be bound to canonical lineage."""

@dataclass(frozen=True)
class ForensicEvidence:
    evidence_id: str
    mission_id: str
    work_id: str
    baseline_sha: str
    failure_fingerprint: str
    forensic_fingerprint: str
    evidence_type: str
    source_refs: tuple[str, ...]
    independent: bool = False

    @property
    def provenance_material(self) -> dict[str, object]:
        return {"evidence_id": self.evidence_id, "mission_id": self.mission_id, "work_id": self.work_id, "baseline_sha": self.baseline_sha, "failure_fingerprint": self.failure_fingerprint, "forensic_fingerprint": self.forensic_fingerprint, "evidence_type": self.evidence_type, "source_refs": self.source_refs, "independent": self.independent}

    @property
    def provenance_hash(self) -> str:
        return hashlib.sha256(json.dumps(self.provenance_material, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

def bind_forensic_evidence(*, identity: CanonicalIdentity, failure_fingerprint: str, forensic_fingerprint: str, evidence_type: str, source_refs: Iterable[str], evidence_id: str, independent: bool = False) -> ForensicEvidence:
    if not isinstance(failure_fingerprint, str) or len(failure_fingerprint) != 64:
        raise ForensicEvidenceError("failure_fingerprint must be SHA-256")
    if not isinstance(forensic_fingerprint, str) or len(forensic_fingerprint) != 64:
        raise ForensicEvidenceError("forensic_fingerprint must be SHA-256")
    if not isinstance(evidence_id, str) or not evidence_id.strip():
        raise ForensicEvidenceError("evidence_id is required")
    if not isinstance(evidence_type, str) or not evidence_type.strip():
        raise ForensicEvidenceError("evidence_type is required")
    refs = tuple(source_refs)
    if not refs or any(not isinstance(ref, str) or not ref.strip() for ref in refs):
        raise ForensicEvidenceError("source_refs are required")
    if len(set(refs)) != len(refs):
        raise ForensicEvidenceError("duplicate source_refs")
    return ForensicEvidence(evidence_id=evidence_id.strip(), mission_id=identity.mission_id, work_id=identity.work_id, baseline_sha=identity.baseline_sha, failure_fingerprint=failure_fingerprint, forensic_fingerprint=forensic_fingerprint, evidence_type=evidence_type.strip(), source_refs=tuple(ref.strip() for ref in refs), independent=independent)

def evidence_is_bound_to_identity(evidence: ForensicEvidence, identity: CanonicalIdentity) -> bool:
    return evidence.mission_id == identity.mission_id and evidence.work_id == identity.work_id and evidence.baseline_sha == identity.baseline_sha

def assert_evidence_lineage(evidence: ForensicEvidence, identity: CanonicalIdentity) -> None:
    if not evidence_is_bound_to_identity(evidence, identity):
        raise ForensicEvidenceError("evidence lineage does not match canonical identity")
