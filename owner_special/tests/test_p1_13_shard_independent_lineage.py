import pytest

from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.ten_billion_federation import build_ten_billion_projection
from owner_special.research_os_friend.p1_13_shard_independent_lineage import (
    ShardIndependentLineageError,
    assert_shard_independent_lineage,
    project_shard_independent_lineage,
)


def ident():
    return CanonicalIdentity(
        mission_id="m-001",
        work_id="w-001",
        baseline_sha="b" * 40,
        request_id="req-1",
        admission_id="adm-1",
        evidence_id="ev-1",
        artifact_id="art-1",
        decision_id="dec-1",
    )


def test_lineage_excludes_partition_from_canonical_identity():
    i = ident()
    f = build_ten_billion_projection()
    a = f.address(namespace=i.mission_id, project_id="project-42")
    lineage = project_shard_independent_lineage(
        federation=f, address=a, identity=i
    )
    assert lineage.mission_id == i.mission_id
    assert lineage.work_id == i.work_id
    assert lineage.baseline_sha == i.baseline_sha
    assert lineage.identity_fingerprint == i.fingerprint()
    assert len(lineage.lineage_fingerprint) == 64


def test_lineage_round_trip_validates():
    i = ident()
    f = build_ten_billion_projection()
    a = f.address(namespace=i.mission_id, project_id="project-42")
    lineage = project_shard_independent_lineage(
        federation=f, address=a, identity=i
    )
    assert_shard_independent_lineage(lineage, i)


def test_wrong_work_fails_closed():
    i = ident()
    f = build_ten_billion_projection()
    a = f.address(namespace=i.mission_id, project_id="project-42")
    lineage = project_shard_independent_lineage(
        federation=f, address=a, identity=i
    )
    other = CanonicalIdentity(
        mission_id=i.mission_id,
        work_id="w-other",
        baseline_sha=i.baseline_sha,
        request_id=i.request_id,
        admission_id=i.admission_id,
        evidence_id=i.evidence_id,
        artifact_id=i.artifact_id,
        decision_id=i.decision_id,
    )
    with pytest.raises(ShardIndependentLineageError):
        assert_shard_independent_lineage(lineage, other)
