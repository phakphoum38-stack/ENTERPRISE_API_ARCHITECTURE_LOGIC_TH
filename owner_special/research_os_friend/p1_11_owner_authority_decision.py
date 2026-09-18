"""P1-11 Owner Authority decision acknowledgement.

Represents an explicit human Owner Authority decision over an existing
Authority Packet. It is an acknowledgement/projection only: it does not
perform approval, merge, Git mutation, or CI mutation.
"""
from __future__ import annotations

from dataclasses import dataclass

from .canonical_identity_federation import CanonicalIdentity, CanonicalIdentityError
from .p1_10_owner_authority_packet_projection import OwnerAuthorityPacketProjection


class P1OwnerDecisionError(CanonicalIdentityError):
    """Raised when an owner decision cannot be safely correlated."""


@dataclass(frozen=True)
class OwnerAuthorityDecision:
    packet_digest: str
    work_id: str
    mission_id: str
    baseline_sha: str
    exact_sha: str
    owner_id: str
    decision: str
    decision_evidence_id: str
    acknowledged: bool


def acknowledge_owner_decision(
    *,
    identity: CanonicalIdentity,
    packet: OwnerAuthorityPacketProjection,
    owner_id: str,
    decision: str,
    decision_evidence_id: str,
) -> OwnerAuthorityDecision:
    if packet.identity_fingerprint != identity.fingerprint:
        raise P1OwnerDecisionError("owner decision identity mismatch")
    if packet.work_id != identity.work_id:
        raise P1OwnerDecisionError("owner decision work mismatch")
    if packet.mission_id != identity.mission_id:
        raise P1OwnerDecisionError("owner decision mission mismatch")
    if packet.baseline_sha != identity.baseline_sha:
        raise P1OwnerDecisionError("owner decision baseline mismatch")
    if packet.exact_sha == identity.baseline_sha:
        raise P1OwnerDecisionError("owner decision target equals protected baseline")
    if packet.owner_authority_granted or packet.merge_authorized:
        raise P1OwnerDecisionError("invalid automated authority escalation")
    if not owner_id:
        raise P1OwnerDecisionError("owner_id_required")
    if decision not in {"APPROVE", "REJECT", "HOLD"}:
        raise P1OwnerDecisionError("invalid_owner_decision")
    if not decision_evidence_id:
        raise P1OwnerDecisionError("decision_evidence_id_required")

    return OwnerAuthorityDecision(
        packet_digest=packet.packet_digest,
        work_id=identity.work_id,
        mission_id=identity.mission_id,
        baseline_sha=identity.baseline_sha,
        exact_sha=packet.exact_sha,
        owner_id=owner_id,
        decision=decision,
        decision_evidence_id=decision_evidence_id,
        acknowledged=True,
    )


def assert_owner_decision_lineage(
    decision: OwnerAuthorityDecision,
    identity: CanonicalIdentity,
) -> None:
    if decision.work_id != identity.work_id:
        raise P1OwnerDecisionError("owner decision work mismatch")
    if decision.mission_id != identity.mission_id:
        raise P1OwnerDecisionError("owner decision mission mismatch")
    if decision.baseline_sha != identity.baseline_sha:
        raise P1OwnerDecisionError("owner decision baseline mismatch")
    if decision.exact_sha == identity.baseline_sha:
        raise P1OwnerDecisionError("owner decision target equals protected baseline")
    if not decision.acknowledged:
        raise P1OwnerDecisionError("owner decision not acknowledged")
