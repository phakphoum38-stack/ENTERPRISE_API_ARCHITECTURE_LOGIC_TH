"""Tests for the HTTP-to-control-plane adapter."""
from decimal import Decimal
import os
import unittest

from budgets import BudgetLimit
from execution_contract import MeasuredExecution
from resource_control_http import HTTPPrincipal, ResourceControlHTTPAdapter
from resource_control_plane import ResourceControlPlane
from resource_governance import Entitlement, Limit, QuotaDimension, Usage, Window


class ResourceControlHTTPAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ.setdefault("RESEARCH_OS_API_KEY_PEPPER", "test-http-resource-control-pepper")
        plane = ResourceControlPlane()
        plane.register_principal(
            "user-1",
            Entitlement(
                "pro",
                scopes=frozenset({"agent:run", "memory:read"}),
                limits=(Limit(QuotaDimension.REQUESTS, Window.HOUR, 10),),
                max_concurrency=2,
            ),
            BudgetLimit("USD", Decimal("10.00")),
        )
        self.plane = plane
        self.adapter = ResourceControlHTTPAdapter(plane)
        self.principal = HTTPPrincipal("user-1", frozenset({"agent:run", "memory:read"}))

    def test_normalize_defaults_and_scope_subset(self):
        request = self.adapter.normalize(
            {
                "request_id": "req-http",
                "prompt": "hello",
                "estimated_cost": "1.25",
                "scopes": ["agent:run"],
                "available_providers": ["local", "openai-compatible"],
            },
            self.principal,
        )
        self.assertEqual(request.principal_id, "user-1")
        self.assertEqual(request.objective, "hello")
        self.assertEqual(request.usage, Usage(requests=1))
        self.assertEqual(request.estimated_cost, Decimal("1.25"))
        self.assertEqual(request.currency, "USD")
        self.assertEqual(request.scopes, frozenset({"agent:run"}))
        self.assertEqual(request.available_providers, ("local", "openai-compatible"))

    def test_normalize_rejects_scope_escalation(self):
        with self.assertRaises(ValueError):
            self.adapter.normalize(
                {
                    "request_id": "req-scope",
                    "objective": "hello",
                    "scopes": ["owner:admin"],
                },
                self.principal,
            )

    def test_normalize_rejects_unknown_usage_dimension(self):
        with self.assertRaises(ValueError):
            self.adapter.normalize(
                {
                    "request_id": "req-usage",
                    "objective": "hello",
                    "usage": {"requests": 1, "unknown_units": 2},
                },
                self.principal,
            )

    def test_execute_delegates_to_single_control_plane(self):
        result = self.adapter.execute(
            {
                "request_id": "req-execute",
                "objective": "hello",
                "usage": {"requests": 1, "concurrent_jobs": 0},
                "estimated_cost": "2.00",
                "currency": "usd",
                "scopes": ["agent:run"],
                "available_providers": ["local"],
            },
            self.principal,
            lambda route: MeasuredExecution(
                {"provider": route["provider"], "model": route["model"], "text": "ok"},
                Usage(requests=1, concurrent_jobs=0),
                Decimal("1.25"),
                "USD",
            ),
        )
        self.assertEqual(result.text, "ok")
        self.assertEqual(result.cost, Decimal("1.25"))
        self.assertEqual(result.currency, "USD")
        self.assertEqual(len(self.plane.ledger()), 1)
        self.assertEqual(len(self.plane.evidence()), 1)


if __name__ == "__main__":
    unittest.main()
