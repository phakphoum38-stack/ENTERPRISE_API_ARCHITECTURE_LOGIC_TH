import os
import unittest
from decimal import Decimal

from budgets import BudgetLimit
from resource_control_http import ResourceControlHTTPAdapter
from resource_control_plane import ResourceControlPlane
from resource_governance import Entitlement, Limit, QuotaDimension, Window


class APIKeyRuntimeContractTests(unittest.TestCase):
    def setUp(self):
        os.environ["RESEARCH_OS_API_KEY_PEPPER"] = "test-only-pepper"
        self.plane = ResourceControlPlane()
        self.plane.register_principal(
            "developer-1",
            Entitlement(
                "developer",
                scopes=frozenset({"agent:run"}),
                limits=(Limit(QuotaDimension.REQUESTS, Window.HOUR, 10),),
                max_concurrency=2,
            ),
            BudgetLimit("USD", Decimal("10.00")),
        )
        self.adapter = ResourceControlHTTPAdapter(self.plane)

    def test_issued_key_authenticates_and_preserves_entitlement_boundary(self):
        record, secret = self.plane.create_api_key("developer-1", {"agent:run"})
        principal = self.adapter.authenticate_api_key(secret, required_scope="agent:run")
        self.assertEqual(principal.principal_id, "developer-1")
        self.assertEqual(principal.scopes, frozenset({"agent:run"}))
        with self.assertRaises(PermissionError):
            self.adapter.authenticate_api_key(secret, required_scope="owner:admin")
        self.plane.api_keys.revoke(record.key_id)
        with self.assertRaises(PermissionError):
            self.adapter.authenticate_api_key(secret)


if __name__ == "__main__":
    unittest.main()
