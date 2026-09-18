from __future__ import annotations
import hashlib, pytest
from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.p1_05_aeos_verification_projection import AEOSVerificationProjection
from owner_special.research_os_friend.p1_06_aeos_certification_projection import P1CertificationError, assert_aeos_certification_lineage, project_aeos_certification

def sha(v:str)->str:return hashlib.sha256(v.encode()).hexdigest()
def identity(): return CanonicalIdentity(mission_id="m-p1-06",work_id="w-p1-06",baseline_sha="a"*40,task_id="task-p1-06",run_id="run-p1-06",attempt_id="attempt-p1-06")
def verification(i): return AEOSVerificationProjection(i.work_id,i.mission_id,i.baseline_sha,i.fingerprint,"evidence-p1-06",("evidence:p1-06",),"VERIFIED",sha("verification"),sha("execution"))

def test_projects_verified_evidence():
    i=identity(); r=project_aeos_certification(identity=i,verification=verification(i),certification_status="CERTIFIED",certification_fingerprint=sha("certification")); assert r.work_id==i.work_id; assert r.certification_status=="CERTIFIED"; assert len(r.certification_hash)==64; assert_aeos_certification_lineage(r,i)

def test_unverified_evidence_fails_closed():
    i=identity(); v=verification(i); v=AEOSVerificationProjection(v.work_id,v.mission_id,v.baseline_sha,v.identity_fingerprint,v.evidence_id,v.evidence_refs,"HOLD",v.verification_fingerprint,v.execution_binding_hash)
    with pytest.raises(P1CertificationError,match="VERIFIED"): project_aeos_certification(identity=i,verification=v,certification_status="CERTIFIED",certification_fingerprint=sha("certification"))

def test_cross_identity_fails_closed():
    i=identity(); other=CanonicalIdentity(mission_id="other",work_id="other",baseline_sha=i.baseline_sha,task_id="task-other",run_id="run-other",attempt_id="attempt-other")
    with pytest.raises(P1CertificationError,match="identity"): project_aeos_certification(identity=other,verification=verification(i),certification_status="CERTIFIED",certification_fingerprint=sha("certification"))
