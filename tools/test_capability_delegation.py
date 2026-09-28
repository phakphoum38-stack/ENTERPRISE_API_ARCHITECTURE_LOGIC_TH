import unittest

from tools.capability_delegation import (
    CANONICAL_DELEGATIONS,
    get_delegation,
    get_operation,
    validate_delegations,
)


class CapabilityDelegationTests(unittest.TestCase):
    def test_all_partial_capabilities_have_one_canonical_delegation_entry(self) -> None:
        self.assertEqual(validate_delegations(), ())
        self.assertEqual(
            {item.capability_id for item in CANONICAL_DELEGATIONS},
            {"friend", "agent", "github", "factory_v3", "assurance"},
        )

    def test_mutating_operations_cannot_be_declared_read_only(self) -> None:
        self.assertEqual(get_operation("friend", "ask friend").action_class, "MUTATION")
        self.assertEqual(get_operation("friend", "run agent").action_class, "MUTATION")
        self.assertEqual(get_operation("agent", "run agent").action_class, "MUTATION")
        self.assertEqual(
            get_operation("factory_v3", "execute factory plan").action_class,
            "MUTATION",
        )

    def test_read_only_operations_are_explicit(self) -> None:
        self.assertEqual(
            get_operation("github", "inspect repository").action_class,
            "READ_ONLY",
        )
        self.assertEqual(
            get_operation("github", "inspect artifacts").action_class,
            "READ_ONLY",
        )
        self.assertEqual(
            get_operation("friend", "inspect status").action_class,
            "READ_ONLY",
        )

    def test_assurance_is_evidence_authority_not_execution_authority(self) -> None:
        binding = get_delegation("assurance")
        self.assertFalse(binding.execution_supported)
        self.assertEqual(binding.operations, ())

    def test_unknown_action_fails_closed(self) -> None:
        with self.assertRaises(KeyError) as raised:
            get_operation("github", "merge pull request")
        self.assertIn("unsupported action", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
