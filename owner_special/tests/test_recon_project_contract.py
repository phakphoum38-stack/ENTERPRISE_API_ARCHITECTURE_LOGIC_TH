from __future__ import annotations

import pytest

from owner_special.research_os_friend.autobot_governance import GovernanceError
from owner_special.research_os_friend.recon_project_contract import (
    AssuranceLevel,
    ProjectCreationContract,
    ProjectLifecycle,
    validate_project_creation,
)

_SHA = "a" * 40


def make_contract(**overrides):
    values = {
        "project_id": "recon-project-001",
        "project_name": "Research OS RECON",
        "owner": "Research OS Team",
        "repository": "phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH",
        "default_branch": "main",
        "initial_commit": _SHA,
        "protocol_version": "protocol-10-v1",
        "purpose": "bounded project creation assurance",
        "boundary": "RECON may inspect and validate; it cannot authorize release",
        "contract": "identity, evidence, recovery and governance are explicit",
        "invariants": ("identity", "evidence", "lineage", "unknown_never_pass"),
        "evidence_requirements": ("exact_sha", "deterministic_result"),
        "dependencies": (),
        "lifecycle": ProjectLifecycle.PROPOSED,
        "assurance_level": AssuranceLevel.P0_IDENTITY,
        "recovery_defined": True,
        "governance_defined": True,
        "authority_defined": True,
    }
    values.update(overrides)
    return ProjectCreationContract(**values)


def test_valid_creation_contract_has_no_failures():
    assert validate_project_creation(make_contract()) == ()


def test_identity_is_exact_repository_and_initial_commit():
    contract = make_contract()
    assert contract.identity_key.endswith(f"@{_SHA}")


def test_missing_recovery_is_rejected():
    assert "missing_recovery" in make_contract(recovery_defined=False).validate_creation()


def test_missing_governance_is_rejected():
    assert "missing_governance" in make_contract(governance_defined=False).validate_creation()


def test_missing_authority_boundary_is_rejected():
    assert "missing_authority_boundary" in make_contract(authority_defined=False).validate_creation()


def test_unknown_initial_commit_fails_closed():
    with pytest.raises(GovernanceError):
        make_contract(initial_commit="not-a-sha")


def test_duplicate_invariants_fail_closed():
    with pytest.raises(GovernanceError):
        make_contract(invariants=("identity", "identity"))


def test_recon_cannot_enter_authorized_or_released():
    contract = make_contract()
    assert contract.can_transition(ProjectLifecycle.AUTHORIZED) is False
    assert contract.can_transition(ProjectLifecycle.RELEASED) is False


def test_failed_project_can_only_enter_recovery():
    contract = make_contract(lifecycle=ProjectLifecycle.FAILED)
    assert contract.can_transition(ProjectLifecycle.RECOVERY) is True
    assert contract.can_transition(ProjectLifecycle.VERIFYING) is False


def test_recovery_returns_to_verifying_only():
    contract = make_contract(lifecycle=ProjectLifecycle.RECOVERY)
    assert contract.can_transition(ProjectLifecycle.VERIFYING) is True
    assert contract.can_transition(ProjectLifecycle.RELEASED) is False


def test_terminal_retirement_cannot_transition():
    contract = make_contract(lifecycle=ProjectLifecycle.RETIRED)
    assert contract.can_transition(ProjectLifecycle.PROPOSED) is False


def test_protocol_depth_is_metadata_not_release_authority():
    contract = make_contract(assurance_level=AssuranceLevel.P10_CONTINUOUS)
    assert contract.assurance_level == AssuranceLevel.P10_CONTINUOUS
    assert contract.can_transition(ProjectLifecycle.RELEASED) is False
