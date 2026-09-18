"""P1-06 verification certification projection for the existing AEOS boundary."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from .canonical_identity_federation import CanonicalIdentity, CanonicalIdentityError
from .p1_05_aeos_verification_projection import AEOSVerificationProjection

class P1CertificationError(CanonicalIdentityError):
    """Raised when certification evidence cannot be safely projected."""

@dataclass(frozen=True)
class AEOSCertificationProjection:
    work_id: str
    mission_id: str
    baseline_sha: str
    identity_fingerprint: str
    evidence_id: str
    verification_status: str
    verification_fingerprint: str
    certification_status: str
    certification_fingerprint: str
    projection_hash: str

    @property
    def certification_hash(self) -> str:
        material = {"work_id":self.work_id,"mission_id":self.mission_id,"baseline_sha":self.baseline_sha,
                    "identity_fingerprint":self.identity_fingerprint,"evidence_id":self.evidence_id,
                    "verification_status":self.verification_status,"verification_fingerprint":self.verification_fingerprint,
                    "certification_status":self.certification_status,"certification_fingerprint":self.certification_fingerprint,
                    "projection_hash":self.projection_hash}
        return hashlib.sha256(json.dumps(material,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def project_aeos_certification(*, identity: CanonicalIdentity, verification: AEOSVerificationProjection,
                               certification_status: str, certification_fingerprint: str) -> AEOSCertificationProjection:
    if verification.identity_fingerprint != identity.fingerprint:
        raise P1CertificationError("certification identity fingerprint mismatch")
    if verification.work_id != identity.work_id:
        raise P1CertificationError("certification work lineage mismatch")
    if verification.mission_id != identity.mission_id:
        raise P1CertificationError("certification mission lineage mismatch")
    if verification.baseline_sha != identity.baseline_sha:
        raise P1CertificationError("certification baseline lineage mismatch")
    if verification.verification_status.strip().upper() != "VERIFIED":
        raise P1CertificationError("certification requires VERIFIED verification status")
    if not isinstance(certification_status,str) or not certification_status.strip():
        raise P1CertificationError("certification_status is required")
    if not isinstance(certification_fingerprint,str) or len(certification_fingerprint)!=64:
        raise P1CertificationError("certification_fingerprint must be SHA-256")
    return AEOSCertificationProjection(verification.work_id,verification.mission_id,verification.baseline_sha,
        verification.identity_fingerprint,verification.evidence_id,verification.verification_status,
        verification.verification_fingerprint,certification_status.strip(),certification_fingerprint,verification.projection_hash)

def assert_aeos_certification_lineage(certification: AEOSCertificationProjection, identity: CanonicalIdentity) -> None:
    if certification.identity_fingerprint != identity.fingerprint:
        raise P1CertificationError("certification identity fingerprint mismatch")
    if certification.work_id != identity.work_id:
        raise P1CertificationError("certification work lineage mismatch")
    if certification.mission_id != identity.mission_id:
        raise P1CertificationError("certification mission lineage mismatch")
    if certification.baseline_sha != identity.baseline_sha:
        raise P1CertificationError("certification baseline lineage mismatch")
