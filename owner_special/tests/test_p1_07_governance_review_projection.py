from __future__ import annotations

import hashlib

import pytest

from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.p1_05_aeos_verification_projection import AEOSVerificationProjection
from owner_special.research_os_friend.p1_06_aeos_certification_projection import (
    AEOSCertificationProjection,
)
from owner_special.research_os_friend.p1_07_governance_review_projection import (
    P1GovernanceReviewError,
    assert_governance_review_lineage,
    project_governance_review,
)


def _identity() -> CanonicalIdentity:
    return CanonicalIdentity(
        mission_id="mission-1",
        work_id="work-1",
        baseline_sha="a" * 40,
        task_id="task-1",
        run_id="run-1",
        attempt_id="attempt-1",
        request_id="request-1",
        admission_id="admission-1",
        evidence_id="evidence-1",
        artifact_id="artifact-1",
        decision_id="decision-1",
    )


def _certification(identity: CanonicalIdentity, status: str = "CERTIFIED") -> AEOSCertificationProjection:
    verification = AEOSVerificationProjection(
        work_id=identity.work_id,
        mission_id=identity.mission_id,
        baseline_sha=identity.baseline_sha,
        identity_fingerprint=identity.fingerprint,
        evidence_id=identity.evidence_id or "evidence-1",
        evidence_refs=("forensic-1", "resource-1"),
        verification_status="VERIFIED",
        verification_fingerprint="b" * 64,
        execution_binding_hash="c" * 64,
        projection_hash="d" * 64,
    )
    return AEOSCertificationProjection(
        work_id=verification.work_id,
        mission_id=verification.mission_id,
        baseline_sha=verification.baseline_sha,
        identity_fingerprint=verification.identity_fingerprint,
        evidence_id=verification.evidence_id,
        verification_status=verification.verification_status,
        verification_fingerprint=verification.verification_fingerprint,
        certification_status=status,
        certification_fingerprint="e" * 64,
        projection_hash=verification.projection_hash,
    )


def test_projects_certified_execution_to_ready_for_review() -> None:
    identity = _identity()
    review = project_governance_review(
        identity=identity,
        certification=_certification(identity),
        review_fingerprint="f" * 64,
    )
    assert review.review_status == "READY_FOR_REVIEW"
    assert review.certification_status == "CERTIFIED"
    assert len(review.review_hash) == 64
    assert_governance_review_lineage(review, identity)


def test_non_certified_execution_fails_closed() -> None:
    identity = _identity()
    with pytest.raises(P1GovernanceReviewError):
        project_governance_review(
            identity=identity,
            certification=_certification(identity, "PENDING"),
            review_fingerprint="f" * 64,
        )


def test_cross_lineage_fails_closed() -> None:
    identity = _identity()
    other = CanonicalIdentity(
        mission_id="mission-2",
        work_id="work-1",
        baseline_sha=identity.baseline_sha,
        task_id=identity.task_id,
        run_id=identity.run_id,
        attempt_id=identity.attempt_id,
    )
    with pytest.raises(P1GovernanceReviewError):
        project_governance_review(
            identity=other,
            certification=_certification(identity),
            review_fingerprint="f" * 64,
        )


def test_invalid_review_fingerprint_fails_closed() -> None:
    identity = _identity()
    with pytest.raises(P1GovernanceReviewError):
        project_governance_review(
            identity=identity,
            certification=_certification(identity),
            review_fingerprint="not-sha256",
        )


def test_review_status_cannot_be_authority() -> None:
    identity = _identity()
    with pytest.raises(P1GovernanceReviewError):
        project_governance_review(
            identity=identity,
            certification=_certification(identity),
            review_status="OWNER_AUTHORITY",
            review_fingerprint="f" * 64,
        )


def test_review_hash_is_deterministic() -> None:
    identity = _identity()
    left = project_governance_review(
        identity=identity,
        certification=_certification(identity),
        review_fingerprint="f" * 64,
    )
    right = project_governance_review(
        identity=identity,
        certification=_certification(identity),
        review_fingerprint="f" * 64,
    )
    assert left == right
    assert left.review_hash == right.review_hash
