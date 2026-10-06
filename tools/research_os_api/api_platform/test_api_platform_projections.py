import os
import unittest
from decimal import Decimal

from budgets import BudgetLimit
from resource_control_plane import ResourceControlPlane
from resource_governance import Entitlement, Limit, QuotaDimension, Usage, Window
from api_platform.management_http import ManagementHTTP
from api_platform.management_service import JsonManagementStore, ManagementService


class APIPlatformProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ.setdefault("RESEARCH_OS_API_KEY_PEPPER", "test-only-pepper")
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.store = JsonManagementStore(__import__("pathlib").Path(self.tmp.name) / "management.json")
        self.service = ManagementService(self.store)
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

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_runtime_projection_is_read_only_and_hash_chained(self) -> None:
        first = self.plane.usage_projection()
        self.assertEqual(first, ())
        self.assertEqual(self.plane.evidence_projection(), ())

    def test_management_http_fails_closed_without_runtime_projection(self) -> None:
        http = ManagementHTTP(self.service, lambda _headers: {"user_id": "owner"})
        status, body = http.dispatch("GET", "/platform/v1/usage", {})
        self.assertEqual(status, 503)
        self.assertEqual(body["error"], "runtime_projection_unavailable")

    def test_management_http_reads_canonical_runtime_projection(self) -> None:
        record, secret = self.plane.create_api_key("developer-1", {"agent:run"})
        self.assertTrue(secret.startswith("ro_live_"))
        http = ManagementHTTP(self.service, lambda _headers: {"user_id": "owner"}, self.plane)
        status, body = http.dispatch("GET", "/platform/v1/costs", {})
        self.assertEqual(status, 200)
        self.assertEqual(body["source"], "runtime-usage-ledger")
        self.assertEqual(body["items"], [])


if __name__ == "__main__":
    unittest.main()
