from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.p1_04_execution_evidence_binding import ExecutionEvidenceBinding
from owner_special.research_os_friend.p1_21_cross_project_evidence_boundary import project_p1_21, P121Error
def test_p1_21_projection():
    i=CanonicalIdentity("m","w","a"*40)
    b=ExecutionEvidenceBinding(i,"1"*64,"EV-21","2"*64,"VERIFIED",("ref",),"3"*64)
    p=project_p1_21(identity=i,bindings=[b],fingerprint="4"*64)
    assert p.evidence_ids==("EV-21",) and len(p.projection_hash)==64
def test_p1_21_fails_closed():
    i=CanonicalIdentity("m","w","a"*40); o=CanonicalIdentity("x","w","a"*40)
    b=ExecutionEvidenceBinding(o,"1"*64,"EV-X","2"*64,"VERIFIED",("ref",),"3"*64)
    try: project_p1_21(identity=i,bindings=[b],fingerprint="4"*64)
    except P121Error: return
    raise AssertionError("cross-lineage evidence must fail closed")
