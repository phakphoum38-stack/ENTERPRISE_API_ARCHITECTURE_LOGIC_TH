from tools.capability_delegation import (
    CANONICAL_DELEGATIONS,
    get_delegation,
    get_operation,
    validate_delegations,
)


def test_all_partial_capabilities_have_one_canonical_delegation_entry() -> None:
    assert validate_delegations() == ()
    assert {item.capability_id for item in CANONICAL_DELEGATIONS} == {
        "friend",
        "agent",
        "github",
        "factory_v3",
        "assurance",
    }


def test_mutating_operations_cannot_be_declared_read_only() -> None:
    assert get_operation("friend", "ask friend").action_class == "MUTATION"
    assert get_operation("friend", "run agent").action_class == "MUTATION"
    assert get_operation("agent", "run agent").action_class == "MUTATION"
    assert get_operation("factory_v3", "execute factory plan").action_class == "MUTATION"


def test_read_only_operations_are_explicit() -> None:
    assert get_operation("github", "inspect repository").action_class == "READ_ONLY"
    assert get_operation("github", "inspect artifacts").action_class == "READ_ONLY"
    assert get_operation("friend", "inspect status").action_class == "READ_ONLY"


def test_assurance_is_evidence_authority_not_execution_authority() -> None:
    binding = get_delegation("assurance")
    assert binding.execution_supported is False
    assert binding.operations == ()


def test_unknown_action_fails_closed() -> None:
    try:
        get_operation("github", "merge pull request")
    except KeyError as exc:
        assert "unsupported action" in str(exc)
    else:
        raise AssertionError("unknown action must fail closed")
