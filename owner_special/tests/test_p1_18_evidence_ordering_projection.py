from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.p1_04_execution_evidence_binding import ExecutionEvidenceBinding
from owner_special.research_os_friend.p1_18_evidence_ordering_projection import project_p1_18, P118Error


def test_p1_18_projection():
    i = CanonicalIdentity(mission_id="m", work_id="w", baseline_sha="a"*40)
    b = ExecutionEvidenceBinding(
        identity=i, resource_binding_hash="1"*64, evidence_id="EV-18",
        provenance_hash="2"*64, verification_status="VERIFIED",
        evidence_refs=("ref",), verification_fingerprint="3"*64
    )
    p = project_p1_18(identity=i, bindings=[b], fingerprint="4"*64)
    assert p.evidence_ids == ("EV-18",)
    assert len(p.projection_hash) == 64


def test_p1_18_fails_closed_on_lineage():
    i = CanonicalIdentity(mission_id="m", work_id="w", baseline_sha="a"*40)
    other = CanonicalIdentity(mission_id="x", work_id="w", baseline_sha="a"*40)
    b = ExecutionEvidenceBinding(
        identity=other, resource_binding_hash="1"*64, evidence_id="EV-X",
        provenance_hash="2"*64, verification_status="VERIFIED",
        evidence_refs=("ref",), verification_fingerprint="3"*64
    )
    try:
        project_p1_18(identity=i, bindings=[b], fingerprint="4"*64)
    except P118Error:
        return
    raise AssertionError("cross-lineage evidence must fail closed")
