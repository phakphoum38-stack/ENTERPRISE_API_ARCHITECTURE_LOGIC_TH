"""Tests for the P1 functional integration boundary."""
from __future__ import annotations
import pytest
from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.p1_08_independent_review_handoff import IndependentReviewHandoff
from owner_special.research_os_friend.p1_09_pre_authority_projection import PreAuthorityProjection
from owner_special.research_os_friend.p1_10_owner_authority_packet_projection import OwnerAuthorityPacketProjection
from owner_special.research_os_friend.p1_11_owner_authority_decision import OwnerAuthorityDecision
from owner_special.research_os_friend.p1_functional_integration import P1FunctionalIntegrationError,assert_p1_functional_integration,integrate_p1_governance_chain
BASELINE="1"*40; TARGET="2"*40; WORK="work-p1-integration"; MISSION="mission-p1"
def ident(): return CanonicalIdentity(MISSION,WORK,BASELINE)
def handoff(): return IndependentReviewHandoff(work_id=WORK,mission_id=MISSION,baseline_sha=BASELINE,identity_fingerprint=ident().fingerprint(),evidence_id="EV-001",review_status="READY_FOR_REVIEW",review_fingerprint="f"*64,review_target_sha=TARGET,independent_review_status="PASS",independent_review_digest="a"*64,recommendation="PROCEED TO PRE-AUTHORITY",handoff_hash="h"*64)
def pre(): return PreAuthorityProjection(gate_id="GATE-001",iteration_id="ITER-001",source_sha=TARGET,work_id=WORK,mission_id=MISSION,baseline_sha=BASELINE,identity_fingerprint=ident().fingerprint(),evidence_ids=("EV-001",),decision="READY_FOR_AUTHORITY",packet_digest="b"*64,remaining_risks=(),remaining_assumptions=(),assurance_debt=())
def packet(): return OwnerAuthorityPacketProjection(work_id=WORK,mission_id=MISSION,baseline_sha=BASELINE,identity_fingerprint=ident().fingerprint(),exact_sha=TARGET,packet_digest="c"*64,recommended_decision="APPROVE",owner_authority_granted=False,merge_authorized=False)
def decision(): return OwnerAuthorityDecision("c"*64,WORK,MISSION,BASELINE,TARGET,"OWNER-001","APPROVE","DECISION-EVIDENCE-001",True)
def run(): return integrate_p1_governance_chain(identity=ident(),handoff=handoff(),pre_authority=pre(),packet=packet(),decision=decision())
def test_complete_chain(): assert run().exact_sha==TARGET and len(run().integration_fingerprint)==64
def test_trace_revalidates(): assert_p1_functional_integration(run(),ident())
@pytest.mark.parametrize("field,value",[("work_id","other"),("mission_id","other"),("baseline_sha","3"*40)])
def test_lineage_fail_closed(field,value):
    d=decision().__class__(**{**decision().__dict__,field:value})
    with pytest.raises(P1FunctionalIntegrationError): integrate_p1_governance_chain(identity=ident(),handoff=handoff(),pre_authority=pre(),packet=packet(),decision=d)
def test_review_target_fail_closed():
    h=handoff().__class__(**{**handoff().__dict__,"review_target_sha":"4"*40})
    with pytest.raises(P1FunctionalIntegrationError): integrate_p1_governance_chain(identity=ident(),handoff=h,pre_authority=pre(),packet=packet(),decision=decision())
def test_pre_authority_must_be_ready():
    p=pre().__class__(**{**pre().__dict__,"decision":"HOLD"})
    with pytest.raises(P1FunctionalIntegrationError): integrate_p1_governance_chain(identity=ident(),handoff=handoff(),pre_authority=p,packet=packet(),decision=decision())
def test_packet_digest_must_match():
    d=decision().__class__(**{**decision().__dict__,"packet_digest":"d"*64})
    with pytest.raises(P1FunctionalIntegrationError): integrate_p1_governance_chain(identity=ident(),handoff=handoff(),pre_authority=pre(),packet=packet(),decision=d)
@pytest.mark.parametrize("field",["owner_authority_granted","merge_authorized"])
def test_automation_cannot_escalate(field):
    p=packet().__class__(**{**packet().__dict__,field:True})
    with pytest.raises(P1FunctionalIntegrationError): integrate_p1_governance_chain(identity=ident(),handoff=handoff(),pre_authority=pre(),packet=p,decision=decision())
def test_protected_baseline_cannot_be_target():
    p=packet().__class__(**{**packet().__dict__,"exact_sha":BASELINE}); d=decision().__class__(**{**decision().__dict__,"exact_sha":BASELINE})
    with pytest.raises(P1FunctionalIntegrationError): integrate_p1_governance_chain(identity=ident(),handoff=handoff(),pre_authority=pre(),packet=p,decision=d)
def test_unacknowledged_decision_fails():
    d=decision().__class__(**{**decision().__dict__,"acknowledged":False})
    with pytest.raises(P1FunctionalIntegrationError): integrate_p1_governance_chain(identity=ident(),handoff=handoff(),pre_authority=pre(),packet=packet(),decision=d)
def test_tampered_trace_fails():
    t=run(); bad=t.__class__(**{**t.__dict__,"identity_fingerprint":"e"*64})
    with pytest.raises(P1FunctionalIntegrationError): assert_p1_functional_integration(bad,ident())
