"""P1-07 governance/review readiness projection for the existing AEOS boundary.

This module only packages already-certified lineage for the existing review path.
It does not grant authority, approve, merge, dispatch, or mutate AEOS/Git/CI.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from .canonical_identity_federation import CanonicalIdentity, CanonicalIdentityError
from .p1_06_aeos_certification_projection import (
    AEOSCertificationProjection,
)


class P1GovernanceReviewError(CanonicalIdentityError):
    """Raised when certified evidence cannot be safely handed to review."""


@dataclass(frozen=True)
class GovernanceReviewProjection:
    work_id: str
    mission_id: str
    baseline_sha: str
    identity_fingerprint: str
    evidence_id: str
    certification_status: str
    certification_fingerprint: str
    review_status: str
    review_fingerprint: str
    projection_hash: str

    @property
    def review_hash(self) -> str:
        material = {
            "work_id": self.work_id,
            "mission_id": self.mission_id,
            "baseline_sha": self.baseline_sha,
            "identity_fingerprint": self.identity_fingerprint,
            "evidence_id": self.evidence_id,
            "certification_status": self.certification_status,
            "certification_fingerprint": self.certification_fingerprint,
            "review_status": self.review_status,
            "review_fingerprint": self.review_fingerprint,
            "projection_hash": self.projection_hash,
        }
        return hashlib.sha256(
            json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


def project_governance_review(
    *,
    identity: CanonicalIdentity,
    certification: AEOSCertificationProjection,
    review_status: str = "READY_FOR_REVIEW",
    review_fingerprint: str,
) -> GovernanceReviewProjection:
    """Project certified execution into the existing human/independent review boundary."""
    if certification.identity_fingerprint != identity.fingerprint:
        raise P1GovernanceReviewError("review identity fingerprint mismatch")
    if certification.work_id != identity.work_id:
        raise P1GovernanceReviewError("review work lineage mismatch")
    if certification.mission_id != identity.mission_id:
        raise P1GovernanceReviewError("review mission lineage mismatch")
    if certification.baseline_sha != identity.baseline_sha:
        raise P1GovernanceReviewError("review baseline lineage mismatch")
    if certification.certification_status.strip().upper() != "CERTIFIED":
        raise P1GovernanceReviewError("governance review requires CERTIFIED certification status")
    if not isinstance(review_status, str) or review_status.strip().upper() != "READY_FOR_REVIEW":
        raise P1GovernanceReviewError("review_status must be READY_FOR_REVIEW")
    if not isinstance(review_fingerprint, str) or len(review_fingerprint) != 64:
        raise P1GovernanceReviewError("review_fingerprint must be SHA-256")

    return GovernanceReviewProjection(
        work_id=certification.work_id,
        mission_id=certification.mission_id,
        baseline_sha=certification.baseline_sha,
        identity_fingerprint=certification.identity_fingerprint,
        evidence_id=certification.evidence_id,
        certification_status=certification.certification_status,
        certification_fingerprint=certification.certification_fingerprint,
        review_status=review_status.strip(),
        review_fingerprint=review_fingerprint,
        projection_hash=certification.certification_hash,
    )


def assert_governance_review_lineage(
    review: GovernanceReviewProjection,
    identity: CanonicalIdentity,
) -> None:
    if review.identity_fingerprint != identity.fingerprint:
        raise P1GovernanceReviewError("review identity fingerprint mismatch")
    if review.work_id != identity.work_id:
        raise P1GovernanceReviewError("review work lineage mismatch")
    if review.mission_id != identity.mission_id:
        raise P1GovernanceReviewError("review mission lineage mismatch")
    if review.baseline_sha != identity.baseline_sha:
        raise P1GovernanceReviewError("review baseline lineage mismatch")
    if review.review_status.strip().upper() != "READY_FOR_REVIEW":
        raise P1GovernanceReviewError("review projection is not READY_FOR_REVIEW")
