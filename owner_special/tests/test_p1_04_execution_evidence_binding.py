"""Tests for P1-04 execution/evidence/verification binding."""
from __future__ import annotations

import hashlib

import pytest

from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.forensic_evidence_binding import bind_forensic_evidence
from owner_special.research_os_friend.p1_resource_execution_binding import (
    ResourceExecutionBinding,
)
from owner_special.research_os_friend.p1_04_execution_evidence_binding import (
    P1EvidenceBindingError,
    bind_execution_evidence,
    assert_execution_evidence_lineage,
)


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _identity() -> CanonicalIdentity:
    return CanonicalIdentity(
        mission_id="m-p1-04",
        work_id="w-p1-04",
        baseline_sha="b" * 40,
        task_id="task-p1-04",
        run_id="run-p1-04",
        attempt_id="attempt-p1-04",
        request_id="request-p1-04",
        admission_id="admission-p1-04",
        evidence_id="evidence-p1-04",
    )


def _resource(identity: CanonicalIdentity) -> ResourceExecutionBinding:
    from owner_special.research_os_friend.resource_admission_binding import ResourceAdmissionBinding

    admission = ResourceAdmissionBinding(
        request_id="request-p1-04",
        admission_id="admission-p1-04",
        principal_id="owner",
        canonical=identity,
        provider="test",
        model="mock",
    )
    return ResourceExecutionBinding(
        resource=admission,
        status="allowed",
        provider="test",
        model="mock",
        ledger_hash=_sha("ledger"),
        evidence_hash=_sha("evidence"),
    )


def _evidence(identity: CanonicalIdentity):
    return bind_forensic_evidence(
        identity=identity,
        failure_fingerprint=_sha("failure"),
        forensic_fingerprint=_sha("forensic"),
        evidence_type="verification",
        source_refs=("ledger:" + _sha("ledger"), "forensic:" + _sha("forensic")),
        evidence_id=identity.evidence_id,
    )


def test_binds_existing_execution_and_evidence():
    identity = _identity()
    binding = bind_execution_evidence(
        identity=identity,
        resource=_resource(identity),
        evidence=_evidence(identity),
        verification_status="VERIFIED",
        evidence_refs=("verification:" + _sha("verification"),),
        verification_fingerprint=_sha("verification"),
    )
    assert binding.identity == identity
    assert binding.evidence_id == identity.evidence_id
    assert binding.evidence_refs
    assert len(binding.binding_hash) == 64
    assert_execution_evidence_lineage(binding, identity)


def test_cross_lineage_resource_fails_closed():
    identity = _identity()
    other = CanonicalIdentity(
        mission_id="other",
        work_id="other",
        baseline_sha=identity.baseline_sha,
        task_id="task-other",
        run_id="run-other",
        attempt_id="attempt-other",
    )
    with pytest.raises(P1EvidenceBindingError, match="resource execution"):
        bind_execution_evidence(
            identity=identity,
            resource=_resource(other),
            evidence=_evidence(identity),
            verification_status="VERIFIED",
            verification_fingerprint=_sha("verification"),
        )


def test_cross_lineage_evidence_fails_closed():
    identity = _identity()
    other = CanonicalIdentity(
        mission_id="other",
        work_id="other",
        baseline_sha=identity.baseline_sha,
        task_id="task-other",
        run_id="run-other",
        attempt_id="attempt-other",
    )
    with pytest.raises(Exception):
        bind_execution_evidence(
            identity=identity,
            resource=_resource(identity),
            evidence=_evidence(other),
            verification_status="VERIFIED",
            verification_fingerprint=_sha("verification"),
        )


def test_invalid_verification_fingerprint_fails_closed():
    identity = _identity()
    with pytest.raises(P1EvidenceBindingError, match="verification_fingerprint"):
        bind_execution_evidence(
            identity=identity,
            resource=_resource(identity),
            evidence=_evidence(identity),
            verification_status="VERIFIED",
            verification_fingerprint="not-a-hash",
        )
