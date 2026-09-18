import pytest

from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.ten_billion_federation import build_ten_billion_projection
from owner_special.research_os_friend.p1_14_project_namespace_isolation import (
    ProjectNamespaceIsolationError,
    assert_namespace_isolation,
    isolate_project_namespace,
)


def ident(mission="m-001"):
    return CanonicalIdentity(
        mission_id=mission,
        work_id="w-001",
        baseline_sha="b" * 40,
        request_id="req-1",
        admission_id="adm-1",
        evidence_id="ev-1",
        artifact_id="art-1",
        decision_id="dec-1",
    )


def test_namespace_isolation_round_trip():
    i = ident()
    f = build_ten_billion_projection()
    a = f.address(namespace=i.mission_id, project_id="project-42")
    result = isolate_project_namespace(federation=f, identity=i, address=a)
    assert result.namespace == i.mission_id
    assert result.project_id == "project-42"
    assert result.identity_fingerprint == i.fingerprint()
    assert len(result.namespace_fingerprint) == 64
    assert_namespace_isolation(result, i)


def test_cross_namespace_project_fails_closed():
    i = ident("m-001")
    f = build_ten_billion_projection()
    a = f.address(namespace="m-002", project_id="project-42")
    with pytest.raises(ProjectNamespaceIsolationError):
        isolate_project_namespace(federation=f, identity=i, address=a)


def test_same_project_id_different_namespaces_remain_distinct():
    f = build_ten_billion_projection()
    a = f.address(namespace="m-001", project_id="project-42")
    b = f.address(namespace="m-002", project_id="project-42")
    assert a.key() != b.key()
