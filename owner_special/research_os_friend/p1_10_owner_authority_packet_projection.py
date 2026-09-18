"""P1-10 Owner Authority Packet projection.

Builds the existing AEOS AuthorityPacket from a READY_FOR_AUTHORITY
pre-authority projection. This remains a preparation-only boundary.
"""
from __future__ import annotations

from dataclasses import dataclass

from .canonical_identity_federation import CanonicalIdentity, CanonicalIdentityError
from .p1_08_independent_review_handoff import IndependentReviewHandoff
from .p1_09_pre_authority_projection import PreAuthorityProjection
from tools.aeos_authority_packet import AuthorityPacket, packet_digest


class P1AuthorityPacketError(CanonicalIdentityError):
    """Raised when the owner-authority packet cannot be safely projected."""


@dataclass(frozen=True)
class OwnerAuthorityPacketProjection:
    work_id: str
    mission_id: str
    baseline_sha: str
    identity_fingerprint: str
    exact_sha: str
    packet_digest: str
    recommended_decision: str
    owner_authority_granted: bool
    merge_authorized: bool


def project_owner_authority_packet(
    *,
    identity: CanonicalIdentity,
    pre_authority: PreAuthorityProjection,
    handoff: IndependentReviewHandoff,
    original_change: str,
    original_failure: str,
    root_cause: str,
    root_cause_proof: tuple[str, ...],
    fix_attempts: tuple[str, ...],
    final_fix: str,
    failed_controls_history: tuple[str, ...],
    resolved_failures: tuple[str, ...],
    new_regressions: tuple[str, ...],
    provenance: tuple[str, ...],
    evidence_integrity: tuple[str, ...],
    forensic_result: str,
    remaining_risks: tuple[str, ...],
    remaining_assumptions: tuple[str, ...],
    assurance_debt: tuple[str, ...],
    recommended_decision: str = "APPROVE",
) -> OwnerAuthorityPacketProjection:
    if pre_authority.identity_fingerprint != identity.fingerprint:
        raise P1AuthorityPacketError("authority packet identity fingerprint mismatch")
    if pre_authority.work_id != identity.work_id:
        raise P1AuthorityPacketError("authority packet work lineage mismatch")
    if pre_authority.mission_id != identity.mission_id:
        raise P1AuthorityPacketError("authority packet mission lineage mismatch")
    if pre_authority.baseline_sha != identity.baseline_sha:
        raise P1AuthorityPacketError("authority packet baseline lineage mismatch")
    if pre_authority.decision != "READY_FOR_AUTHORITY":
        raise P1AuthorityPacketError("authority packet requires READY_FOR_AUTHORITY")
    if handoff.independent_review_status != "PASS":
        raise P1AuthorityPacketError("authority packet requires independent review PASS")
    if handoff.review_target_sha != pre_authority.source_sha:
        raise P1AuthorityPacketError("authority packet target/source SHA mismatch")

    packet = AuthorityPacket(
        original_change=original_change,
        original_failure=original_failure,
        root_cause=root_cause,
        root_cause_proof=root_cause_proof,
        fix_attempts=fix_attempts,
        final_fix=final_fix,
        failed_controls_history=failed_controls_history,
        resolved_failures=resolved_failures,
        new_regressions=new_regressions,
        exact_sha=pre_authority.source_sha,
        provenance=provenance,
        evidence_integrity=evidence_integrity,
        forensic_result=forensic_result,
        independent_review="PASS",
        remaining_risks=remaining_risks,
        remaining_assumptions=remaining_assumptions,
        assurance_debt=assurance_debt,
        recommended_decision=recommended_decision,
    )
    digest = packet_digest(packet)

    return OwnerAuthorityPacketProjection(
        work_id=identity.work_id,
        mission_id=identity.mission_id,
        baseline_sha=identity.baseline_sha,
        identity_fingerprint=identity.fingerprint,
        exact_sha=pre_authority.source_sha,
        packet_digest=digest,
        recommended_decision=recommended_decision,
        owner_authority_granted=False,
        merge_authorized=False,
    )


def assert_owner_authority_packet_lineage(
    projection: OwnerAuthorityPacketProjection,
    identity: CanonicalIdentity,
) -> None:
    if projection.identity_fingerprint != identity.fingerprint:
        raise P1AuthorityPacketError("authority packet identity fingerprint mismatch")
    if projection.work_id != identity.work_id:
        raise P1AuthorityPacketError("authority packet work lineage mismatch")
    if projection.mission_id != identity.mission_id:
        raise P1AuthorityPacketError("authority packet mission lineage mismatch")
    if projection.baseline_sha != identity.baseline_sha:
        raise P1AuthorityPacketError("authority packet baseline lineage mismatch")
    if projection.exact_sha == projection.baseline_sha:
        raise P1AuthorityPacketError("authority packet target equals protected baseline")
    if projection.owner_authority_granted:
        raise P1AuthorityPacketError("automation cannot grant owner authority")
    if projection.merge_authorized:
        raise P1AuthorityPacketError("automation cannot grant merge authorization")
