"""P1-05 project execution evidence into the existing AEOS verification boundary."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from .aeos_durable_work_graph import WorkItem
from .canonical_identity_federation import CanonicalIdentity, CanonicalIdentityError
from .p1_04_execution_evidence_binding import ExecutionEvidenceBinding, P1EvidenceBindingError, assert_execution_evidence_lineage

class P1AEOSVerificationError(CanonicalIdentityError):
    """Raised when an AEOS verification projection is unsafe."""

@dataclass(frozen=True)
class AEOSVerificationProjection:
    work_id: str
    mission_id: str
    baseline_sha: str
    identity_fingerprint: str
    evidence_id: str
    evidence_refs: tuple[str, ...]
    verification_status: str
    verification_fingerprint: str
    execution_binding_hash: str

    @property
    def projection_hash(self) -> str:
        material = {"work_id": self.work_id, "mission_id": self.mission_id, "baseline_sha": self.baseline_sha,
                    "identity_fingerprint": self.identity_fingerprint, "evidence_id": self.evidence_id,
                    "evidence_refs": self.evidence_refs, "verification_status": self.verification_status,
                    "verification_fingerprint": self.verification_fingerprint,
                    "execution_binding_hash": self.execution_binding_hash}
        return hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def project_aeos_verification(*, identity: CanonicalIdentity, work_item: WorkItem,
                               execution_evidence: ExecutionEvidenceBinding) -> AEOSVerificationProjection:
    try:
        assert_execution_evidence_lineage(execution_evidence, identity)
    except P1EvidenceBindingError as exc:
        raise P1AEOSVerificationError(str(exc)) from exc
    if work_item.work_id != identity.work_id:
        raise P1AEOSVerificationError("AEOS work_id does not match canonical identity")
    if work_item.mission_id != identity.mission_id:
        raise P1AEOSVerificationError("AEOS mission_id does not match canonical identity")
    if work_item.baseline_sha != identity.baseline_sha:
        raise P1AEOSVerificationError("AEOS baseline SHA does not match canonical identity")
    if work_item.state in {"COMPLETED", "BLOCKED", "QUARANTINED", "CANCELLED"}:
        raise P1AEOSVerificationError("terminal AEOS work item cannot receive a verification projection")
    if not execution_evidence.evidence_id or not execution_evidence.evidence_refs:
        raise P1AEOSVerificationError("verification projection requires evidence")
    if not isinstance(execution_evidence.verification_fingerprint, str) or len(execution_evidence.verification_fingerprint) != 64:
        raise P1AEOSVerificationError("verification fingerprint must be SHA-256")
    refs = tuple(dict.fromkeys((*work_item.evidence_refs, *execution_evidence.evidence_refs)))
    return AEOSVerificationProjection(work_item.work_id, work_item.mission_id, work_item.baseline_sha,
        identity.fingerprint, execution_evidence.evidence_id, refs, execution_evidence.verification_status,
        execution_evidence.verification_fingerprint, execution_evidence.binding_hash)

def assert_aeos_verification_projection(projection: AEOSVerificationProjection,
                                        identity: CanonicalIdentity, work_item: WorkItem) -> None:
    if projection.work_id != identity.work_id or projection.work_id != work_item.work_id:
        raise P1AEOSVerificationError("verification work lineage mismatch")
    if projection.mission_id != identity.mission_id or projection.mission_id != work_item.mission_id:
        raise P1AEOSVerificationError("verification mission lineage mismatch")
    if projection.baseline_sha != identity.baseline_sha or projection.baseline_sha != work_item.baseline_sha:
        raise P1AEOSVerificationError("verification baseline lineage mismatch")
    if projection.identity_fingerprint != identity.fingerprint:
        raise P1AEOSVerificationError("verification identity fingerprint mismatch")
