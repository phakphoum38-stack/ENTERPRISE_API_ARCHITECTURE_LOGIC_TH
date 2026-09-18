import pytest

from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.p1_functional_integration import P1FunctionalIntegrationTrace
from owner_special.research_os_friend.ten_billion_federation import build_ten_billion_projection
from owner_special.research_os_friend.p1_12_cross_shard_correlation import (
    CrossShardCorrelationError,
    correlate_cross_shard,
)


def ident():
    return CanonicalIdentity(
        mission_id="m-001",
        work_id="w-project-42",
        baseline_sha="b" * 40,
        request_id="req-1",
        admission_id="adm-1",
        evidence_id="ev-1",
        artifact_id="art-1",
        decision_id="dec-1",
    )


def trace(identity):
    return P1FunctionalIntegrationTrace(
        identity_fingerprint=identity.fingerprint(),
        work_id=identity.work_id,
        mission_id=identity.mission_id,
        baseline_sha=identity.baseline_sha,
        exact_sha="a" * 40,
        handoff_status="PASS",
        pre_authority_decision="READY_FOR_AUTHORITY",
        packet_digest="c" * 64,
        owner_decision="HOLD",
        owner_id="owner-1",
        acknowledged=True,
        integration_fingerprint="d" * 64,
    )


def test_cross_shard_correlation_is_deterministic():
    i = ident()
    f = build_ten_billion_projection()
    a = f.address(namespace=i.mission_id, project_id="project-42")
    c1 = correlate_cross_shard(federation=f, address=a, identity=i, integration=trace(i))
    c2 = correlate_cross_shard(federation=f, address=a, identity=i, integration=trace(i))
    assert c1 == c2
    assert len(c1.correlation_fingerprint) == 64


def test_namespace_mismatch_fails_closed():
    i = ident()
    f = build_ten_billion_projection()
    a = f.address(namespace="other-mission", project_id="project-42")
    with pytest.raises(CrossShardCorrelationError):
        correlate_cross_shard(federation=f, address=a, identity=i, integration=trace(i))
