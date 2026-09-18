from __future__ import annotations

import pytest

from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.p1_10_owner_authority_packet_projection import OwnerAuthorityPacketProjection
from owner_special.research_os_friend.p1_11_owner_authority_decision import (
    P1OwnerDecisionError,
    acknowledge_owner_decision,
    assert_owner_decision_lineage,
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


def packet(i: CanonicalIdentity) -> OwnerAuthorityPacketProjection:
    return OwnerAuthorityPacketProjection(
        work_id=i.work_id,
        mission_id=i.mission_id,
        baseline_sha=i.baseline_sha,
        identity_fingerprint=i.fingerprint,
        exact_sha="f" * 40,
        packet_digest="b" * 64,
        recommended_decision="APPROVE",
        owner_authority_granted=False,
        merge_authorized=False,
    )


def test_acknowledges_explicit_owner_decision() -> None:
    i = identity()
    result = acknowledge_owner_decision(
        identity=i,
        packet=packet(i),
        owner_id="owner-1",
        decision="APPROVE",
        decision_evidence_id="decision-evidence-1",
    )
    assert result.acknowledged is True
    assert result.decision == "APPROVE"
    assert result.exact_sha == "f" * 40
    assert_owner_decision_lineage(result, i)


@pytest.mark.parametrize("decision", ["REJECT", "HOLD"])
def test_non_approve_decisions_are_preserved(decision: str) -> None:
    i = identity()
    result = acknowledge_owner_decision(
        identity=i,
        packet=packet(i),
        owner_id="owner-1",
        decision=decision,
        decision_evidence_id="decision-evidence-1",
    )
    assert result.decision == decision


def test_invalid_decision_fails_closed() -> None:
    i = identity()
    with pytest.raises(P1OwnerDecisionError):
        acknowledge_owner_decision(
            identity=i,
            packet=packet(i),
            owner_id="owner-1",
            decision="MERGE",
            decision_evidence_id="decision-evidence-1",
        )


def test_authority_escalation_is_rejected() -> None:
    i = identity()
    unsafe = OwnerAuthorityPacketProjection(
        **{**packet(i).__dict__, "owner_authority_granted": True}
    )
    with pytest.raises(P1OwnerDecisionError):
        acknowledge_owner_decision(
            identity=i,
            packet=unsafe,
            owner_id="owner-1",
            decision="APPROVE",
            decision_evidence_id="decision-evidence-1",
        )
