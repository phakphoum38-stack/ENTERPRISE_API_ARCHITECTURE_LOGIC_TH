from __future__ import annotations

import pytest

from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.p1_06_aeos_certification_projection import AEOSCertificationProjection
from owner_special.research_os_friend.p1_07_governance_review_projection import project_governance_review
from owner_special.research_os_friend.p1_08_independent_review_handoff import project_independent_review
from owner_special.research_os_friend.p1_09_pre_authority_projection import (
    P1PreAuthorityError,
    assert_pre_authority_lineage,
    project_pre_authority,
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


def handoff(i: CanonicalIdentity):
    review = project_governance_review(
        identity=i,
        certification=certification(i),
        review_fingerprint="e" * 64,
    )
    independent = perform_independent_review(
        ReviewEvidence(
            repository="example/research-os",
            pull_request=500,
            base_sha="a" * 40,
            head_sha="f" * 40,
            protected_baseline="a" * 40,
            changed_files=("x.py",),
            ci_pass=True,
            forensic_pass=True,
            tests_pass=True,
            provenance_pass=True,
            scope_pass=True,
            authority_boundary_pass=True,
            source_identity_pass=True,
            root_cause_verified=True,
        )
    )
    return project_independent_review(
        identity=i,
        review=review,
        independent_review=independent,
    )


def kwargs(i: CanonicalIdentity, h) -> dict:
    return dict(
        identity=i,
        handoff=h,
        gate_id="GATE-P1-09",
        iteration_id="ITER-001",
        source_sha=h.review_target_sha,
        required_waves=("P0", "P1"),
        wave_results=(("P0", "PASS"), ("P1", "PASS")),
        evidence_ids=("1" * 64,),
        provenance_verified=True,
        evidence_integrity_verified=True,
        scope_verified=True,
        root_cause_verified=True,
        assurance_self_check_verified=True,
    )


def test_projects_ready_for_authority_when_existing_gate_is_ready() -> None:
    i = identity()
    result = project_pre_authority(**kwargs(i, handoff(i)))
    assert result.decision == "READY_FOR_AUTHORITY"
    assert len(result.packet_digest) == 64
    assert_pre_authority_lineage(result, i)


def test_review_target_mismatch_fails_closed() -> None:
    i = identity()
    h = handoff(i)
    values = kwargs(i, h)
    values["source_sha"] = "9" * 40
    with pytest.raises(P1PreAuthorityError):
        project_pre_authority(**values)


def test_failed_wave_is_hold_not_authority() -> None:
    i = identity()
    values = kwargs(i, handoff(i))
    values["wave_results"] = (("P0", "PASS"), ("P1", "HOLD"))
    result = project_pre_authority(**values)
    assert result.decision == "HOLD"


def test_failed_assurance_is_blocked() -> None:
    i = identity()
    values = kwargs(i, handoff(i))
    values["assurance_self_check_verified"] = False
    result = project_pre_authority(**values)
    assert result.decision == "BLOCKED"


def test_protected_baseline_cannot_be_authority_target() -> None:
    i = identity()
    values = kwargs(i, handoff(i))
    values["source_sha"] = i.baseline_sha
    values["handoff"] = handoff(i)
    with pytest.raises(P1PreAuthorityError):
        project_pre_authority(**values)
