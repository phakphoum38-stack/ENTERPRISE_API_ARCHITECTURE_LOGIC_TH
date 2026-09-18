from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.p1_04_execution_evidence_binding import ExecutionEvidenceBinding
from owner_special.research_os_friend.p1_305_federation_evidence_scale_final_release_boundary import project_p1_305
def test_projection():
 i=CanonicalIdentity("m","w","a"*40); b=ExecutionEvidenceBinding(i,"1"*64,"EV-305","2"*64,"VERIFIED",("ref",),"3"*64); p=project_p1_305(identity=i,bindings=[b],fingerprint="4"*64); assert len(p.projection_hash)==64
