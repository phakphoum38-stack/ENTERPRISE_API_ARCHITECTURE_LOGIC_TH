from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.project_fleet import FleetProject, ProjectFleet
from owner_special.research_os_friend.distributed_coordination import CoordinationClaim
from owner_special.research_os_friend.ten_billion_federation import (
    DEFAULT_PARTITION_COUNT,
    LOGICAL_PROJECT_CAPACITY,
    TenBillionFederationError,
    build_ten_billion_projection,
)


def identity(project_id="p-001", mission_id="m-001"):
    return CanonicalIdentity(
        mission_id=mission_id,
        work_id=f"w-{project_id}",
        baseline_sha="b" * 40,
        request_id="req-1",
        admission_id="adm-1",
        evidence_id="ev-1",
        artifact_id="art-1",
        decision_id="dec-1",
    )


def test_projection_is_10_billion_without_materializing_projects():
    projection = build_ten_billion_projection()
    assert projection.logical_capacity == 10_000_000_000
    assert projection.logical_capacity == LOGICAL_PROJECT_CAPACITY
    assert projection.partition_count == DEFAULT_PARTITION_COUNT
    assert projection.partition_capacity == 10_000


def test_addressing_is_deterministic():
    projection = build_ten_billion_projection()
    a = projection.address(namespace="m-001", project_id="project-42")
    b = projection.address(namespace="m-001", project_id="project-42")
    assert a == b
    assert 0 <= a.partition_id < projection.partition_count
    assert 0 <= a.slot < projection.partition_capacity


def test_operational_view_remains_bounded():
    projection = build_ten_billion_projection()
    fleet = ProjectFleet(
        (
            FleetProject("project-42", identity("project-42", "m-001")),
        )
    )
    projection.validate_operational_view(fleet)
    assert fleet.capacity == 100


def test_namespace_mismatch_fails_closed():
    projection = build_ten_billion_projection()
    address = projection.address(namespace="m-001", project_id="project-42")
    try:
        projection.correlation_key(
            address=address,
            identity=identity("project-42", "m-002"),
        )
    except TenBillionFederationError:
        pass
    else:
        raise AssertionError("expected namespace mismatch to fail closed")


def test_stale_claim_fails_closed():
    projection = build_ten_billion_projection()
    ident = identity()
    address = projection.address(namespace="m-001", project_id="p-001")
    claim = CoordinationClaim(
        project_id="p-001",
        identity=ident,
        owner_id="owner-1",
        epoch=2,
        claim_id="claim-1",
    )
    try:
        projection.validate_claim(
            address=address,
            identity=ident,
            claim=claim,
            expected_epoch=3,
        )
    except TenBillionFederationError:
        pass
    else:
        raise AssertionError("expected stale claim to fail closed")
