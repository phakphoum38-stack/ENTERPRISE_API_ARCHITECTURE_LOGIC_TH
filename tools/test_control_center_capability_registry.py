import unittest

from tools.control_center_capability_registry import (
    CANONICAL_CAPABILITY_BINDINGS,
    get_capability,
    iter_capabilities,
    validate_registry,
)


class ControlCenterCapabilityRegistryTests(unittest.TestCase):
    def test_registry_is_unique_and_structurally_complete(self):
        self.assertEqual(validate_registry(), ())
        self.assertEqual(
            len({item.capability_id for item in CANONICAL_CAPABILITY_BINDINGS}),
            len(CANONICAL_CAPABILITY_BINDINGS),
        )

    def test_control_center_is_the_canonical_control_surface(self):
        binding = get_capability("control_center")
        self.assertEqual(binding.domain, "CONTROL")
        self.assertEqual(binding.status, "CANONICAL_WIRED")

    def test_major_engines_remain_delegated(self):
        for capability in ("friend", "agent", "github", "factory_v3", "assurance"):
            binding = get_capability(capability)
            self.assertEqual(binding.status, "PARTIAL")
            self.assertNotEqual(binding.runtime_ref, binding.ui_ref)

    def test_domain_filter_is_deterministic(self):
        self.assertEqual(
            tuple(item.capability_id for item in iter_capabilities(domain="factory")),
            ("factory_v3",),
        )
        self.assertEqual(
            tuple(item.capability_id for item in iter_capabilities(domain="friend")),
            ("friend",),
        )


if __name__ == "__main__":
    unittest.main()
