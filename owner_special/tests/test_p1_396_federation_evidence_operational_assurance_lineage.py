from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.p1_04_execution_evidence_binding import ExecutionEvidenceBinding
from owner_special.research_os_friend.p1_396_federation_evidence_operational_assurance_lineage import project_p1_396
def test_projection():
 i=CanonicalIdentity("m","w","a"*40); b=ExecutionEvidenceBinding(i,"1"*64,"EV-396","2"*64,"VERIFIED",("ref",),"3"*64); p=project_p1_396(identity=i,bindings=[b],fingerprint="4"*64); assert len(p.projection_hash)==64
