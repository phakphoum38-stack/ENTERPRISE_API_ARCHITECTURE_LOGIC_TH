from tools.aeos_assurance_universe_compiler import (
    ASSURANCE_FAMILIES,
    DIMENSIONS,
    LIFECYCLE,
    NEVER_PASS,
    assertion_id,
    compile_addresses,
    compile_catalog,
    validate_observation,
)


DOMAINS = ("D001", "D051", "D113", "D120")


def expect_value_error(call, message):
    try:
        call()
    except ValueError as exc:
        assert message in str(exc), str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_default_catalogs_are_nonempty_and_unique():
    for catalog in (ASSURANCE_FAMILIES, DIMENSIONS, LIFECYCLE):
        assert catalog
        assert all(isinstance(item, str) and item.strip() for item in catalog)
        assert len(catalog) == len(set(catalog))


def test_address_identity_is_deterministic():
    first = assertion_id("D051", "evidence_integrity", "evidence_ref", "VERIFY")
    second = assertion_id("D051", "evidence_integrity", "evidence_ref", "VERIFY")
    assert first == second
    assert first.startswith("AX-D051-EVIDENCE_INTEGRITY-EVIDENCE_REF-VERIFY-")


def test_compiler_accepts_variable_catalog_sizes():
    families = ("family_a", "family_b")
    dimensions = ("dim_a", "dim_b", "dim_c")
    lifecycle = ("OBSERVE", "VERIFY")
    addresses = compile_addresses(
        ("D1", "D2"),
        families=families,
        dimensions=dimensions,
        lifecycle=lifecycle,
    )
    assert len(addresses) == 2 * 2 * 3 * 2
    assert len({a.assertion_id for a in addresses}) == len(addresses)


def test_empty_catalogs_are_rejected():
    expect_value_error(lambda: compile_addresses(("D1",), families=()), "must not be empty")
    expect_value_error(lambda: compile_addresses(("D1",), dimensions=()), "must not be empty")
    expect_value_error(lambda: compile_addresses(("D1",), lifecycle=()), "must not be empty")
    expect_value_error(lambda: compile_addresses(()), "must not be empty")


def test_blank_or_non_string_catalog_entries_are_rejected():
    expect_value_error(lambda: compile_addresses(("D1",), families=(" ",)), "non-empty strings")
    expect_value_error(lambda: compile_addresses(("D1",), dimensions=("",)), "non-empty strings")
    expect_value_error(lambda: compile_addresses(("D1",), lifecycle=(None,)), "non-empty strings")
    expect_value_error(lambda: compile_addresses((" ",)), "non-empty strings")


def test_duplicate_catalog_entries_are_rejected():
    expect_value_error(
        lambda: compile_addresses(("D1",), families=("same", "same")),
        "must be unique",
    )
    expect_value_error(
        lambda: compile_addresses(("D1",), dimensions=("same", "same")),
        "must be unique",
    )
    expect_value_error(
        lambda: compile_addresses(("D1",), lifecycle=("same", "same")),
        "must be unique",
    )
    expect_value_error(lambda: compile_addresses(("D1", "D1")), "must be unique")


def test_compiler_builds_expected_address_space():
    addresses = compile_addresses(DOMAINS)
    expected = (
        len(DOMAINS)
        * len(ASSURANCE_FAMILIES)
        * len(DIMENSIONS)
        * len(LIFECYCLE)
    )
    assert len(addresses) == expected
    assert len({a.assertion_id for a in addresses}) == len(addresses)


def test_catalog_digest_is_deterministic():
    first = compile_catalog(DOMAINS)
    second = compile_catalog(DOMAINS)
    assert first["address_digest"] == second["address_digest"]
    assert first["address_count"] == second["address_count"]


def test_never_pass_states_are_blocked():
    for state in NEVER_PASS:
        expect_value_error(lambda state=state: validate_observation({"state": state}), "state")


def test_unknown_state_is_blocked():
    expect_value_error(
        lambda: validate_observation({"state": "INVENTED_STATE"}),
        "unknown assurance state",
    )


def test_valid_observation_state_is_not_certification():
    # The compiler only validates vocabulary; it never creates evidence or authority.
    validate_observation({"state": "OBSERVED"})
    validate_observation({"state": "INDEPENDENTLY_VERIFIED"})
