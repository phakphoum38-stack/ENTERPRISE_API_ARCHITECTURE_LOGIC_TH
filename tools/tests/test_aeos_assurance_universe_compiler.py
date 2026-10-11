from tools.aeos_assurance_universe_compiler import (
    ASSURANCE_FAMILIES,
    ASSURANCE_FAMILY_ALIASES,
    DIMENSIONS,
    LIFECYCLE,
    NEVER_PASS,
    assertion_id,
    compile_addresses,
    compile_catalog,
    validate_observation,
)


DOMAINS = ("D001", "D051", "D113", "D120")


def test_catalog_is_exactly_100_by_100():
    assert len(ASSURANCE_FAMILIES) == 100
    assert len(DIMENSIONS) == 100
    assert len(set(ASSURANCE_FAMILIES)) == 100
    assert len(set(DIMENSIONS)) == 100


def test_extra_assurance_concepts_are_preserved_as_explicit_aliases():
    expected = {
        "common_mode_resistance",
        "assurance_completeness",
        "assurance_of_assurance",
        "constitutional_integrity",
        "knowledge_lifecycle_integrity",
    }
    assert set(ASSURANCE_FAMILY_ALIASES) == expected
    assert len(ASSURANCE_FAMILIES) == 100
    for mapping in ASSURANCE_FAMILY_ALIASES.values():
        assert mapping["families"]
        assert set(mapping["families"]) <= set(ASSURANCE_FAMILIES)
        assert mapping["dimensions"]
        assert set(mapping["dimensions"]) <= set(DIMENSIONS)
    assert ASSURANCE_FAMILY_ALIASES["assurance_of_assurance"]["domains"] == ("D113",)
    assert ASSURANCE_FAMILY_ALIASES["knowledge_lifecycle_integrity"]["domains"] == ("D120",)


def test_address_identity_is_deterministic():
    first = assertion_id("D051", "evidence_integrity", "evidence_ref", "VERIFY")
    second = assertion_id("D051", "evidence_integrity", "evidence_ref", "VERIFY")
    assert first == second
    assert first.startswith("AX-D051-EVIDENCE_INTEGRITY-EVIDENCE_REF-VERIFY-")


def test_compiler_builds_expected_address_space():
    addresses = compile_addresses(DOMAINS)
    assert len(addresses) == len(DOMAINS) * 100 * 100 * len(LIFECYCLE)
    assert len({a.assertion_id for a in addresses}) == len(addresses)


def test_catalog_digest_is_deterministic():
    first = compile_catalog(DOMAINS)
    second = compile_catalog(DOMAINS)
    assert first["address_digest"] == second["address_digest"]
    assert first["address_count"] == second["address_count"]


def test_never_pass_states_are_blocked():
    for state in NEVER_PASS:
        try:
            validate_observation({"state": state})
        except ValueError:
            pass
        else:
            raise AssertionError(f"state unexpectedly accepted: {state}")


def test_unknown_state_is_blocked():
    try:
        validate_observation({"state": "INVENTED_STATE"})
    except ValueError:
        pass
    else:
        raise AssertionError("invented assurance state unexpectedly accepted")


def test_valid_observation_state_is_not_certification():
    # The compiler only validates vocabulary; it never creates evidence or authority.
    validate_observation({"state": "OBSERVED"})
    validate_observation({"state": "INDEPENDENTLY_VERIFIED"})
