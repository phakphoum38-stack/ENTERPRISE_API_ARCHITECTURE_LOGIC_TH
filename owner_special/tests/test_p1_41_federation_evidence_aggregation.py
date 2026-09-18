from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.p1_15_cross_partition_evidence_correlation import CrossPartitionEvidenceCorrelation
from owner_special.research_os_friend.p1_41_federation_evidence_aggregation import aggregate_federation_evidence

def test_aggregation_is_deterministic_shape():
    i=CanonicalIdentity("m","w","a"*40)
    c=CrossPartitionEvidenceCorrelation(i,"p",(7,),("EV-1",),("1"*64,),"2"*64)
    a=aggregate_federation_evidence(identity=i,correlation=c,aggregation_fingerprint="3"*64)
    assert len(a.aggregation_hash)==64
