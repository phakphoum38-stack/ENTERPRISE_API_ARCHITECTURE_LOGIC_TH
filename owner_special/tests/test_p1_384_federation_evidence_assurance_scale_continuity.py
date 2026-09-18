from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.p1_04_execution_evidence_binding import ExecutionEvidenceBinding
from owner_special.research_os_friend.p1_384_federation_evidence_assurance_scale_continuity import project_p1_384
def test_projection():
 i=CanonicalIdentity("m","w","a"*40); b=ExecutionEvidenceBinding(i,"1"*64,"EV-384","2"*64,"VERIFIED",("ref",),"3"*64); p=project_p1_384(identity=i,bindings=[b],fingerprint="4"*64); assert len(p.projection_hash)==64
