from __future__ import annotations

from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.p1_06_aeos_certification_projection import AEOSCertificationProjection
from owner_special.research_os_friend.p1_07_governance_review_projection import project_governance_review
from owner_special.research_os_friend.p1_08_independent_review_handoff import (
    P1IndependentReviewError,
    assert_independent_review_handoff,
    project_independent_review,
)
from tools.aeos_independent_reviewer import ReviewEvidence, perform_independent_review


def identity() -> CanonicalIdentity:
    return CanonicalIdentity(
        mission_id="mission-1",
        work_id="work-1",
        baseline_sha="a" * 40,
        task_id="task-1",
        run_id="run-1",
        attempt_id="attempt-1",
    )


def certification(i: CanonicalIdentity) -> AEOSCertificationProjection:
    return AEOSCertificationProjection(
        work_id=i.work_id,
        mission_id=i.mission_id,
        baseline_sha=i.baseline_sha,
        identity_fingerprint=i.fingerprint,
        evidence_id="evidence-1",
        verification_status="VERIFIED",
        verification_fingerprint="b" * 64,
        certification_status="CERTIFIED",
        certification_fingerprint="c" * 64,
        projection_hash="d" * 64,
    )


def independent_review() -> object:
    e = ReviewEvidence(
        repository="example/research-os",
        pull_request=500,
        base_sha="a" * 40,
        head_sha="f" * 40,
        protected_baseline="a" * 40,
        changed_files=("owner_special/research_os_friend/p1_08_independent_review_handoff.py",),
        ci_pass=True,
        forensic_pass=True,
        tests_pass=True,
        provenance_pass=True,
        scope_pass=True,
        authority_boundary_pass=True,
        source_identity_pass=True,
        root_cause_verified=True,
    )
    return perform_independent_review(e)


def test_projects_passed_independent_review() -> None:
    i = identity()
    review = project_governance_review(
        identity=i,
        certification=certification(i),
        review_fingerprint="e" * 64,
    )
    result = project_independent_review(
        identity=i,
        review=review,
        independent_review=independent_review(),
    )
    assert result.independent_review_status == "PASS"
    assert result.review_target_sha == "f" * 40
    assert result.recommendation == "PROCEED TO PRE-AUTHORITY"
    assert len(result.independent_review_hash) == 64
    assert_independent_review_handoff(result, i)


def test_hold_review_fails_closed() -> None:
    i = identity()
    review = project_governance_review(
        identity=i,
        certification=certification(i),
        review_fingerprint="e" * 64,
    )
    evidence = ReviewEvidence(
        repository="example/research-os",
        pull_request=500,
        base_sha="a" * 40,
        head_sha="f" * 40,
        protected_baseline="a" * 40,
        changed_files=("x.py",),
        ci_pass=False,
        forensic_pass=True,
        tests_pass=True,
        provenance_pass=True,
        scope_pass=True,
        authority_boundary_pass=True,
        source_identity_pass=True,
        root_cause_verified=True,
    )
    with __import__("pytest").raises(P1IndependentReviewError):
        project_independent_review(
            identity=i,
            review=review,
            independent_review=perform_independent_review(evidence),
        )


def test_owner_authority_and_merge_remain_locked() -> None:
    i = identity()
    review = project_governance_review(
        identity=i,
        certification=certification(i),
        review_fingerprint="e" * 64,
    )
    result = project_independent_review(
        identity=i,
        review=review,
        independent_review=independent_review(),
    )
    assert result.recommendation == "PROCEED TO PRE-AUTHORITY"
    assert result.independent_review_status == "PASS"
