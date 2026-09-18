"""P1 Functional Integration boundary.

Composes existing P1 projections into one side-effect-free integration trace.
This module does not execute work, grant authority, merge Git, mutate CI,
create queues, or create a scheduler.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
from .canonical_identity_federation import CanonicalIdentity, CanonicalIdentityError
from .p1_08_independent_review_handoff import IndependentReviewHandoff
from .p1_09_pre_authority_projection import PreAuthorityProjection
from .p1_10_owner_authority_packet_projection import OwnerAuthorityPacketProjection
from .p1_11_owner_authority_decision import OwnerAuthorityDecision

class P1FunctionalIntegrationError(CanonicalIdentityError):
    """Raised when the P1 integration chain cannot be proven safely."""

@dataclass(frozen=True)
class P1FunctionalIntegrationTrace:
    identity_fingerprint: str
    work_id: str
    mission_id: str
    baseline_sha: str
    exact_sha: str
    handoff_status: str
    pre_authority_decision: str
    packet_digest: str
    owner_decision: str
    owner_id: str
    acknowledged: bool
    integration_fingerprint: str

def _lineage(identity, work_id, mission_id, baseline_sha):
    if work_id != identity.work_id: raise P1FunctionalIntegrationError("integration work lineage mismatch")
    if mission_id != identity.mission_id: raise P1FunctionalIntegrationError("integration mission lineage mismatch")
    if baseline_sha != identity.baseline_sha: raise P1FunctionalIntegrationError("integration baseline lineage mismatch")

def integrate_p1_governance_chain(*, identity: CanonicalIdentity, handoff: IndependentReviewHandoff,
    pre_authority: PreAuthorityProjection, packet: OwnerAuthorityPacketProjection,
    decision: OwnerAuthorityDecision) -> P1FunctionalIntegrationTrace:
    """Prove the completed P1 governance chain is internally correlated."""
    for item in (handoff, pre_authority, packet, decision):
        _lineage(identity, item.work_id, item.mission_id, item.baseline_sha)
    if handoff.independent_review_status != "PASS":
        raise P1FunctionalIntegrationError("integration requires independent review PASS")
    if handoff.review_target_sha != pre_authority.source_sha:
        raise P1FunctionalIntegrationError("handoff/pre-authority target mismatch")
    if pre_authority.decision != "READY_FOR_AUTHORITY":
        raise P1FunctionalIntegrationError("integration requires READY_FOR_AUTHORITY")
    if packet.exact_sha != pre_authority.source_sha:
        raise P1FunctionalIntegrationError("packet target/source mismatch")
    if packet.packet_digest != decision.packet_digest:
        raise P1FunctionalIntegrationError("decision packet digest mismatch")
    if packet.owner_authority_granted:
        raise P1FunctionalIntegrationError("owner authority was granted by automation")
    if packet.merge_authorized:
        raise P1FunctionalIntegrationError("merge authorization was granted by automation")
    if not decision.acknowledged:
        raise P1FunctionalIntegrationError("owner decision is not acknowledged")
    if decision.exact_sha != packet.exact_sha:
        raise P1FunctionalIntegrationError("owner decision target mismatch")
    if decision.exact_sha == identity.baseline_sha:
        raise P1FunctionalIntegrationError("integration target equals protected baseline")
    material="|".join((identity.fingerprint(),handoff.review_evidence_digest,
        pre_authority.packet_digest,packet.packet_digest,decision.decision_evidence_id,decision.decision))
    return P1FunctionalIntegrationTrace(identity.fingerprint(),identity.work_id,identity.mission_id,
        identity.baseline_sha,decision.exact_sha,handoff.independent_review_status,
        pre_authority.decision,packet.packet_digest,decision.decision,decision.owner_id,
        decision.acknowledged,hashlib.sha256(material.encode()).hexdigest())

def assert_p1_functional_integration(trace, identity):
    """Fail closed when an integration trace loses lineage."""
    _lineage(identity,trace.work_id,trace.mission_id,trace.baseline_sha)
    if trace.identity_fingerprint != identity.fingerprint(): raise P1FunctionalIntegrationError("integration identity fingerprint mismatch")
    if trace.exact_sha == identity.baseline_sha: raise P1FunctionalIntegrationError("integration target equals protected baseline")
    if trace.handoff_status != "PASS": raise P1FunctionalIntegrationError("integration trace handoff is not PASS")
    if trace.pre_authority_decision != "READY_FOR_AUTHORITY": raise P1FunctionalIntegrationError("integration trace is not ready for authority")
    if trace.owner_decision not in {"APPROVE","REJECT","HOLD"}: raise P1FunctionalIntegrationError("invalid owner decision in integration trace")
    if not trace.acknowledged: raise P1FunctionalIntegrationError("integration trace is not acknowledged")
