"""P1-08 independent-review handoff projection for the existing AEOS review boundary.

This module binds READY_FOR_REVIEW evidence to the existing independent reviewer.
It remains review-only: no authority, approval, merge, Git, CI, or AEOS mutation.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re

from .canonical_identity_federation import CanonicalIdentity, CanonicalIdentityError
from .p1_07_governance_review_projection import GovernanceReviewProjection
from tools.aeos_independent_reviewer import IndependentReview

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class P1IndependentReviewError(CanonicalIdentityError):
    """Raised when review handoff evidence cannot be safely projected."""


@dataclass(frozen=True)
class IndependentReviewHandoff:
    work_id: str
    mission_id: str
    baseline_sha: str
    identity_fingerprint: str
    evidence_id: str
    review_status: str
    review_fingerprint: str
    review_target_sha: str
    independent_review_status: str
    independent_review_digest: str
    recommendation: str
    handoff_hash: str

    @property
    def independent_review_hash(self) -> str:
        material = {
            "work_id": self.work_id,
            "mission_id": self.mission_id,
            "baseline_sha": self.baseline_sha,
            "identity_fingerprint": self.identity_fingerprint,
            "evidence_id": self.evidence_id,
            "review_status": self.review_status,
            "review_fingerprint": self.review_fingerprint,
            "review_target_sha": self.review_target_sha,
            "independent_review_status": self.independent_review_status,
            "independent_review_digest": self.independent_review_digest,
            "recommendation": self.recommendation,
            "handoff_hash": self.handoff_hash,
        }
        return hashlib.sha256(
            json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


def project_independent_review(
    *,
    identity: CanonicalIdentity,
    review: GovernanceReviewProjection,
    independent_review: IndependentReview,
) -> IndependentReviewHandoff:
    if review.identity_fingerprint != identity.fingerprint:
        raise P1IndependentReviewError("independent review identity fingerprint mismatch")
    if review.work_id != identity.work_id:
        raise P1IndependentReviewError("independent review work lineage mismatch")
    if review.mission_id != identity.mission_id:
        raise P1IndependentReviewError("independent review mission lineage mismatch")
    if review.baseline_sha != identity.baseline_sha:
        raise P1IndependentReviewError("independent review baseline lineage mismatch")
    if review.review_status.strip().upper() != "READY_FOR_REVIEW":
        raise P1IndependentReviewError("independent review requires READY_FOR_REVIEW")
    if independent_review.decision != "PASS":
        raise P1IndependentReviewError("independent review must PASS")
    if independent_review.authority != "REVIEW_ONLY":
        raise P1IndependentReviewError("independent review authority boundary mismatch")
    if independent_review.owner_authority != "NOT GRANTED":
        raise P1IndependentReviewError("owner authority must remain NOT GRANTED")
    if independent_review.merge_authorization != "LOCKED":
        raise P1IndependentReviewError("merge authorization must remain LOCKED")
    if not SHA_RE.fullmatch(independent_review.target_sha):
        raise P1IndependentReviewError("invalid independent review target SHA")
    if independent_review.target_sha == identity.baseline_sha:
        raise P1IndependentReviewError("independent review target must differ from protected baseline")
    if not isinstance(independent_review.evidence_digest, str) or len(independent_review.evidence_digest) != 64:
        raise P1IndependentReviewError("independent review digest must be SHA-256")

    return IndependentReviewHandoff(
        work_id=review.work_id,
        mission_id=review.mission_id,
        baseline_sha=review.baseline_sha,
        identity_fingerprint=review.identity_fingerprint,
        evidence_id=review.evidence_id,
        review_status=review.review_status,
        review_fingerprint=review.review_fingerprint,
        review_target_sha=independent_review.target_sha,
        independent_review_status=independent_review.decision,
        independent_review_digest=independent_review.evidence_digest,
        recommendation=independent_review.recommendation,
        handoff_hash=review.review_hash,
    )


def assert_independent_review_handoff(
    handoff: IndependentReviewHandoff,
    identity: CanonicalIdentity,
) -> None:
    if handoff.identity_fingerprint != identity.fingerprint:
        raise P1IndependentReviewError("independent review identity fingerprint mismatch")
    if handoff.work_id != identity.work_id:
        raise P1IndependentReviewError("independent review work lineage mismatch")
    if handoff.mission_id != identity.mission_id:
        raise P1IndependentReviewError("independent review mission lineage mismatch")
    if handoff.baseline_sha != identity.baseline_sha:
        raise P1IndependentReviewError("independent review baseline lineage mismatch")
    if handoff.review_status.strip().upper() != "READY_FOR_REVIEW":
        raise P1IndependentReviewError("handoff is not READY_FOR_REVIEW")
    if handoff.independent_review_status != "PASS":
        raise P1IndependentReviewError("handoff independent review is not PASS")
