from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.p1_04_execution_evidence_binding import ExecutionEvidenceBinding
from owner_special.research_os_friend.p1_16_40_federation_evidence_projections import project_federation_evidence, P1FederationEvidenceError

def binding(i):
    return ExecutionEvidenceBinding(i,"1"*64,"EV-001","2"*64,"VERIFIED",("ref",),"3"*64)

def test_all_stages_are_bounded():
    i=CanonicalIdentity("m","w","a"*40)
    for stage in range(16,41):
        p=project_federation_evidence(stage,identity=i,bindings=[binding(i)],fingerprint="4"*64)
        assert p.stage==stage and len(p.projection_hash)==64

def test_cross_lineage_fails_closed():
    i=CanonicalIdentity("m","w","a"*40); other=CanonicalIdentity("x","w","a"*40)
    try: project_federation_evidence(16,identity=i,bindings=[binding(other)],fingerprint="4"*64)
    except P1FederationEvidenceError: return
    raise AssertionError("cross-lineage evidence must fail closed")
