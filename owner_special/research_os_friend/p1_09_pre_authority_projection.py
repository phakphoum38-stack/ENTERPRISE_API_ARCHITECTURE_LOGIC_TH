"""P1-09 Pre-Authority packet projection.

Packages an independent-review PASS into the existing AEOS pre-authority gate.
It prepares readiness only; it does not grant Owner Authority or merge access.
"""
from __future__ import annotations

from dataclasses import dataclass

from .canonical_identity_federation import CanonicalIdentity, CanonicalIdentityError
from .p1_08_independent_review_handoff import IndependentReviewHandoff
from tools.aeos_pre_authority_gate import AuthorityPacket, packet_digest, pre_authority_decision


class P1PreAuthorityError(CanonicalIdentityError):
    """Raised when pre-authority readiness cannot be safely projected."""


@dataclass(frozen=True)
class PreAuthorityProjection:
    gate_id: str
    iteration_id: str
    source_sha: str
    work_id: str
    mission_id: str
    baseline_sha: str
    identity_fingerprint: str
    evidence_ids: tuple[str, ...]
    decision: str
    packet_digest: str
    remaining_risks: tuple[str, ...]
    remaining_assumptions: tuple[str, ...]
    assurance_debt: tuple[str, ...]


def project_pre_authority(
    *,
    identity: CanonicalIdentity,
    handoff: IndependentReviewHandoff,
    gate_id: str,
    iteration_id: str,
    source_sha: str,
    required_waves: tuple[str, ...],
    wave_results: tuple[tuple[str, str], ...],
    evidence_ids: tuple[str, ...],
    provenance_verified: bool,
    evidence_integrity_verified: bool,
    scope_verified: bool,
    root_cause_verified: bool,
    assurance_self_check_verified: bool,
    remaining_risks: tuple[str, ...] = (),
    remaining_assumptions: tuple[str, ...] = (),
    assurance_debt: tuple[str, ...] = (),
) -> PreAuthorityProjection:
    if handoff.identity_fingerprint != identity.fingerprint:
        raise P1PreAuthorityError("pre-authority identity fingerprint mismatch")
    if handoff.work_id != identity.work_id:
        raise P1PreAuthorityError("pre-authority work lineage mismatch")
    if handoff.mission_id != identity.mission_id:
        raise P1PreAuthorityError("pre-authority mission lineage mismatch")
    if handoff.baseline_sha != identity.baseline_sha:
        raise P1PreAuthorityError("pre-authority baseline lineage mismatch")
    if handoff.independent_review_status != "PASS":
        raise P1PreAuthorityError("pre-authority requires independent review PASS")
    if handoff.recommendation != "PROCEED TO PRE-AUTHORITY":
        raise P1PreAuthorityError("invalid independent-review recommendation")
    if source_sha != handoff.review_target_sha:
        raise P1PreAuthorityError("pre-authority source SHA must equal reviewed target SHA")
    if not evidence_ids:
        raise P1PreAuthorityError("pre-authority evidence is required")

    packet = AuthorityPacket(
        gate_id=gate_id,
        iteration_id=iteration_id,
        source_sha=source_sha,
        required_waves=required_waves,
        wave_results=wave_results,
        holds=(),
        evidence_ids=evidence_ids,
        provenance_verified=provenance_verified,
        evidence_integrity_verified=evidence_integrity_verified,
        scope_verified=scope_verified,
        root_cause_verified=root_cause_verified,
        independent_review_verified=True,
        assurance_self_check_verified=assurance_self_check_verified,
        remaining_risks=remaining_risks,
        remaining_assumptions=remaining_assumptions,
        assurance_debt=assurance_debt,
    )
    decision = pre_authority_decision(packet)
    if decision not in {"READY_FOR_AUTHORITY", "HOLD", "BLOCKED"}:
        raise P1PreAuthorityError("unexpected pre-authority decision")

    return PreAuthorityProjection(
        gate_id=gate_id,
        iteration_id=iteration_id,
        source_sha=source_sha,
        work_id=identity.work_id,
        mission_id=identity.mission_id,
        baseline_sha=identity.baseline_sha,
        identity_fingerprint=identity.fingerprint,
        evidence_ids=evidence_ids,
        decision=decision,
        packet_digest=packet_digest(packet),
        remaining_risks=remaining_risks,
        remaining_assumptions=remaining_assumptions,
        assurance_debt=assurance_debt,
    )


def assert_pre_authority_lineage(
    projection: PreAuthorityProjection,
    identity: CanonicalIdentity,
) -> None:
    if projection.identity_fingerprint != identity.fingerprint:
        raise P1PreAuthorityError("pre-authority identity fingerprint mismatch")
    if projection.work_id != identity.work_id:
        raise P1PreAuthorityError("pre-authority work lineage mismatch")
    if projection.mission_id != identity.mission_id:
        raise P1PreAuthorityError("pre-authority mission lineage mismatch")
    if projection.baseline_sha != identity.baseline_sha:
        raise P1PreAuthorityError("pre-authority baseline lineage mismatch")
    if projection.source_sha == projection.baseline_sha:
        raise P1PreAuthorityError("pre-authority source equals protected baseline")
