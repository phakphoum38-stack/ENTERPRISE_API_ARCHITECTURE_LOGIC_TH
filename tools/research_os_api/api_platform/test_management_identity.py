"""Regression tests for the independent management identity boundary."""
import unittest

from tools.research_os_api.api_platform.management_identity import (
    ManagementIdentityRegistry,
    ManagementPrincipal,
    PrincipalType,
)


class ManagementIdentityRegistryTests(unittest.TestCase):
    def test_valid_principal_hierarchy(self) -> None:
        registry = ManagementIdentityRegistry()
        registry.register_organization("org-1")
        principal = registry.register_principal(
            ManagementPrincipal("principal-1", "org-1", PrincipalType.USER, "Developer")
        )
        self.assertEqual(registry.get_principal("principal-1"), principal)

    def test_unknown_organization_fails_closed(self) -> None:
        registry = ManagementIdentityRegistry()
        with self.assertRaisesRegex(ValueError, "unknown organization"):
            registry.register_principal(
                ManagementPrincipal("principal-1", "missing", PrincipalType.USER, "Developer")
            )

    def test_duplicate_organization_fails_closed(self) -> None:
        registry = ManagementIdentityRegistry()
        registry.register_organization("org-1")
        with self.assertRaisesRegex(ValueError, "duplicate organization"):
            registry.register_organization("org-1")

    def test_duplicate_principal_fails_closed(self) -> None:
        registry = ManagementIdentityRegistry()
        registry.register_organization("org-1")
        principal = ManagementPrincipal("principal-1", "org-1", PrincipalType.USER, "Developer")
        registry.register_principal(principal)
        with self.assertRaisesRegex(ValueError, "duplicate principal"):
            registry.register_principal(principal)

    def test_empty_ids_fail_closed(self) -> None:
        registry = ManagementIdentityRegistry()
        with self.assertRaisesRegex(ValueError, "organization id is required"):
            registry.register_organization("   ")


if __name__ == "__main__":
    unittest.main()
