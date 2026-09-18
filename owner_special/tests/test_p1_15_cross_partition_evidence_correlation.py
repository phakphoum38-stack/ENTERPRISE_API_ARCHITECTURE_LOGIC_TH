from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.p1_14_project_namespace_isolation import ProjectNamespaceIsolation
from owner_special.research_os_friend.p1_15_cross_partition_evidence_correlation import (
    CrossPartitionEvidenceCorrelationError,
    correlate_cross_partition_evidence,
)


class Binding:
    def __init__(self, identity, evidence_id, binding_hash):
        self.identity = identity
        self.evidence_id = evidence_id
        self.binding_hash = binding_hash


def identity():
    return CanonicalIdentity(mission_id="mission-p1", work_id="work-1", baseline_sha="a" * 40)


def isolation(i):
    return ProjectNamespaceIsolation(
        namespace=i.mission_id,
        project_id="project-1",
        partition_id=7,
        slot=11,
        identity_fingerprint=i.fingerprint(),
        namespace_fingerprint="b" * 64,
    )


def test_correlates_multiple_bindings():
    i = identity()
    result = correlate_cross_partition_evidence(
        identity=i,
        isolation=isolation(i),
        bindings=[
            Binding(i, "EV-001", "1" * 64),
            Binding(i, "EV-002", "2" * 64),
        ],
        correlation_fingerprint="3" * 64,
    )
    assert result.project_id == "project-1"
    assert result.partition_ids == (7,)
    assert result.evidence_ids == ("EV-001", "EV-002")
    assert len(result.correlation_hash) == 64


def test_cross_lineage_fails_closed():
    i = identity()
    other = CanonicalIdentity(mission_id="other", work_id="work-1", baseline_sha="a" * 40)
    try:
        correlate_cross_partition_evidence(
            identity=i,
            isolation=isolation(i),
            bindings=[Binding(other, "EV-001", "1" * 64)],
            correlation_fingerprint="3" * 64,
        )
    except CrossPartitionEvidenceCorrelationError:
        return
    raise AssertionError("cross-lineage evidence must fail closed")


def test_invalid_correlation_fingerprint_fails_closed():
    i = identity()
    try:
        correlate_cross_partition_evidence(
            identity=i,
            isolation=isolation(i),
            bindings=[Binding(i, "EV-001", "1" * 64)],
            correlation_fingerprint="not-sha256",
        )
    except CrossPartitionEvidenceCorrelationError:
        return
    raise AssertionError("invalid correlation fingerprint must fail closed")
