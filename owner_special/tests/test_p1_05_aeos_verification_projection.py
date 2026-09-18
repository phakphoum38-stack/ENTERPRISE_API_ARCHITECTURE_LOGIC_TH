"""Tests for P1-05 AEOS verification projection."""
from __future__ import annotations
import hashlib, pytest
from owner_special.research_os_friend.aeos_durable_work_graph import WorkItem
from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.forensic_evidence_binding import bind_forensic_evidence
from owner_special.research_os_friend.p1_04_execution_evidence_binding import bind_execution_evidence
from owner_special.research_os_friend.p1_05_aeos_verification_projection import P1AEOSVerificationError, assert_aeos_verification_projection, project_aeos_verification
from owner_special.research_os_friend.p1_resource_execution_binding import ResourceExecutionBinding
from owner_special.research_os_friend.resource_admission_binding import ResourceAdmissionBinding

def sha(v: str) -> str: return hashlib.sha256(v.encode()).hexdigest()

def identity() -> CanonicalIdentity:
    return CanonicalIdentity(mission_id="m-p1-05", work_id="w-p1-05", baseline_sha="a"*40,
        task_id="task-p1-05", run_id="run-p1-05", attempt_id="attempt-p1-05")

def work(i: CanonicalIdentity, state: str = "VERIFYING") -> WorkItem:
    return WorkItem(work_id=i.work_id, mission_id=i.mission_id, intent="p1-05 verification",
        baseline_sha=i.baseline_sha, state=state,
        lease_id="lease-p1-05" if state in {"LEASED","RUNNING","VERIFYING","CERTIFYING"} else None,
        evidence_refs=("existing:evidence",))

def evidence_binding(i: CanonicalIdentity):
    admission = ResourceAdmissionBinding(request_id="request-p1-05", admission_id="admission-p1-05",
        principal_id="owner", canonical=i, provider="test", model="mock")
    resource = ResourceExecutionBinding(resource=admission, status="allowed", provider="test", model="mock",
        ledger_hash=sha("ledger"), evidence_hash=sha("evidence"))
    evidence = bind_forensic_evidence(identity=i, failure_fingerprint=sha("failure"),
        forensic_fingerprint=sha("forensic"), evidence_type="verification",
        source_refs=("forensic:"+sha("forensic"),), evidence_id="evidence-p1-05")
    return bind_execution_evidence(identity=i, resource=resource, evidence=evidence,
        verification_status="VERIFIED", verification_fingerprint=sha("verification"))

def test_projects_existing_aeos_work_item_without_mutation():
    i=identity(); item=work(i)
    projection=project_aeos_verification(identity=i, work_item=item, execution_evidence=evidence_binding(i))
    assert projection.work_id == i.work_id
    assert projection.evidence_id == "evidence-p1-05"
    assert len(projection.projection_hash) == 64
    assert_aeos_verification_projection(projection, i, item)

def test_cross_lineage_work_fails_closed():
    i=identity(); other=CanonicalIdentity(mission_id="other", work_id="other", baseline_sha=i.baseline_sha,
        task_id="task-other", run_id="run-other", attempt_id="attempt-other")
    with pytest.raises(P1AEOSVerificationError, match="work_id"):
        project_aeos_verification(identity=i, work_item=work(other), execution_evidence=evidence_binding(i))

def test_baseline_mismatch_fails_closed():
    i=identity()
    item=WorkItem(work_id=i.work_id, mission_id=i.mission_id, intent="p1-05 verification",
        baseline_sha="b"*40, state="VERIFYING", lease_id="lease-p1-05", evidence_refs=("existing:evidence",))
    with pytest.raises(P1AEOSVerificationError, match="baseline"):
        project_aeos_verification(identity=i, work_item=item, execution_evidence=evidence_binding(i))

def test_terminal_work_is_immutable_for_projection():
    i=identity()
    item=WorkItem(work_id=i.work_id, mission_id=i.mission_id, intent="p1-05 verification",
        baseline_sha=i.baseline_sha, state="COMPLETED", evidence_refs=("existing:evidence",))
    with pytest.raises(P1AEOSVerificationError, match="terminal"):
        project_aeos_verification(identity=i, work_item=item, execution_evidence=evidence_binding(i))
