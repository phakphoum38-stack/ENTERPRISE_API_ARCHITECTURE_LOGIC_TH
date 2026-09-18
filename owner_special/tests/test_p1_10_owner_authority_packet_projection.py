from __future__ import annotations

import pytest

from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.p1_08_independent_review_handoff import IndependentReviewHandoff
from owner_special.research_os_friend.p1_09_pre_authority_projection import PreAuthorityProjection
from owner_special.research_os_friend.p1_10_owner_authority_packet_projection import (
    P1AuthorityPacketError,
    assert_owner_authority_packet_lineage,
    project_owner_authority_packet,
)


def identity() -> CanonicalIdentity:
    return CanonicalIdentity(
        mission_id="mission-1",
        work_id="work-1",
        baseline_sha="a" * 40,
        task_id="task-1",
        run_id="run-1",
        attempt_id="attempt-1",
    )


def handoff(i: CanonicalIdentity) -> IndependentReviewHandoff:
    return IndependentReviewHandoff(
        work_id=i.work_id,
        mission_id=i.mission_id,
        baseline_sha=i.baseline_sha,
        identity_fingerprint=i.fingerprint,
        evidence_id="evidence-1",
        review_status="READY_FOR_REVIEW",
        review_fingerprint="b" * 64,
        review_target_sha="f" * 40,
        independent_review_status="PASS",
        independent_review_digest="c" * 64,
        recommendation="PROCEED TO PRE-AUTHORITY",
        handoff_hash="d" * 64,
    )


def pre(i: CanonicalIdentity) -> PreAuthorityProjection:
    return PreAuthorityProjection(
        gate_id="GATE-1",
        iteration_id="ITER-1",
        source_sha="f" * 40,
        work_id=i.work_id,
        mission_id=i.mission_id,
        baseline_sha=i.baseline_sha,
        identity_fingerprint=i.fingerprint,
        evidence_ids=("1" * 64,),
        decision="READY_FOR_AUTHORITY",
        packet_digest="e" * 64,
        remaining_risks=(),
        remaining_assumptions=(),
        assurance_debt=(),
    )


def args(i: CanonicalIdentity) -> dict:
    return dict(
        identity=i,
        pre_authority=pre(i),
        handoff=handoff(i),
        original_change="change",
        original_failure="failure",
        root_cause="root-cause",
        root_cause_proof=("1" * 64,),
        fix_attempts=("attempt-1",),
        final_fix="fix",
        failed_controls_history=("control-1",),
        resolved_failures=("failure-1",),
        new_regressions=(),
        provenance=("prov-1",),
        evidence_integrity=("integrity-1",),
        forensic_result="PASS",
        remaining_risks=(),
        remaining_assumptions=(),
        assurance_debt=(),
    )


def test_projects_existing_authority_packet_without_granting_authority() -> None:
    i = identity()
    result = project_owner_authority_packet(**args(i))
    assert len(result.packet_digest) == 64
    assert result.exact_sha == "f" * 40
    assert result.owner_authority_granted is False
    assert result.merge_authorized is False
    assert_owner_authority_packet_lineage(result, i)


def test_pre_authority_hold_fails_closed() -> None:
    i = identity()
    values = args(i)
    values["pre_authority"] = PreAuthorityProjection(
        **{**pre(i).__dict__, "decision": "HOLD"}
    )
    with pytest.raises(P1AuthorityPacketError):
        project_owner_authority_packet(**values)


def test_target_baseline_fails_closed() -> None:
    i = identity()
    values = args(i)
    values["pre_authority"] = PreAuthorityProjection(
        **{**pre(i).__dict__, "source_sha": i.baseline_sha}
    )
    with pytest.raises(P1AuthorityPacketError):
        project_owner_authority_packet(**values)


def test_automation_cannot_grant_authority() -> None:
    i = identity()
    result = project_owner_authority_packet(**args(i))
    assert result.owner_authority_granted is False
    assert result.merge_authorized is False
