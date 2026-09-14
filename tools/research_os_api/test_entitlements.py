"""Tests for identity-to-entitlement bindings."""
from datetime import datetime, timedelta, timezone
import unittest

from entitlements import EntitlementRegistry, EntitlementState, PrincipalBinding
from resource_governance import Entitlement, Limit, QuotaDimension, QuotaError, Window


class EntitlementRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = EntitlementRegistry()
        self.entitlement = Entitlement(
            tier="pro",
            scopes=frozenset({"chat:execute", "memory:read"}),
            limits=(Limit(QuotaDimension.REQUESTS, Window.MINUTE, 10),),
            priority=5,
            max_concurrency=2,
        )
        self.now = datetime(2026, 9, 14, 15, 0, tzinfo=timezone.utc)

    def test_bind_and_authorize_scope(self) -> None:
        self.registry.bind(PrincipalBinding("user-1", self.entitlement), now=self.now)
        binding = self.registry.authorize_scope("user-1", "chat:execute", now=self.now)
        self.assertEqual(binding.entitlement.tier, "pro")

    def test_missing_scope_fails_closed(self) -> None:
        self.registry.bind(PrincipalBinding("user-1", self.entitlement), now=self.now)
        with self.assertRaisesRegex(QuotaError, "scope_not_entitled"):
            self.registry.authorize_scope("user-1", "factory:execute", now=self.now)

    def test_suspend_and_revoke_fail_closed(self) -> None:
        self.registry.bind(PrincipalBinding("user-1", self.entitlement), now=self.now)
        self.registry.suspend("user-1")
        with self.assertRaisesRegex(QuotaError, "inactive"):
            self.registry.get("user-1", now=self.now)
        self.registry.restore("user-1", now=self.now)
        self.registry.revoke("user-1")
        with self.assertRaisesRegex(QuotaError, "inactive"):
            self.registry.get("user-1", now=self.now)

    def test_expired_binding_cannot_be_bound(self) -> None:
        expired = self.now - timedelta(seconds=1)
        with self.assertRaisesRegex(QuotaError, "inactive"):
            self.registry.bind(
                PrincipalBinding("user-1", self.entitlement, expires_at=expired),
                now=self.now,
            )

    def test_naive_expiry_is_rejected(self) -> None:
        with self.assertRaisesRegex(QuotaError, "timezone-aware"):
            PrincipalBinding(
                "user-1",
                self.entitlement,
                expires_at=datetime(2026, 9, 14, 15, 0),
            )


if __name__ == "__main__":
    unittest.main()
