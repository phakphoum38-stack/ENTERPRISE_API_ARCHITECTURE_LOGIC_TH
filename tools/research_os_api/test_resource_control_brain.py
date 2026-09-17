"""Contract tests for the Brain-to-resource-control boundary."""
from decimal import Decimal
import os
import unittest

from budgets import BudgetLimit
from execution_contract import MeasuredExecution
from resource_control_brain import BrainControlRequest, BrainResourceControlAdapter
from resource_control_plane import ResourceControlPlane
from resource_governance import Entitlement, Limit, QuotaDimension, Usage, Window


class BrainResourceControlTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ.setdefault("RESEARCH_OS_API_KEY_PEPPER", "test-brain-resource-control-pepper")
        self.plane = ResourceControlPlane()
        self.plane.register_principal(
            "owner-1",
            Entitlement(
                "owner",
                scopes=frozenset({"agent:run"}),
                limits=(Limit(QuotaDimension.REQUESTS, Window.HOUR, 10),),
                max_concurrency=4,
            ),
            BudgetLimit("USD", Decimal("10.00")),
        )
        self.adapter = BrainResourceControlAdapter(self.plane)

    def test_brain_workload_becomes_admission_usage(self):
        request = BrainControlRequest(
            request_id="brain-1",
            principal_id="owner-1",
            objective="decompose research",
            leaf_tasks=9,
            parallelism=4,
            estimated_cost=Decimal("2.00"),
            currency="USD",
            scopes=frozenset({"agent:run"}),
            available_providers=("local",),
        )
        result = self.adapter.execute(
            request,
            lambda route: {"provider": route["provider"], "model": route["model"], "text": "ok"},
            measure=lambda value, _route: MeasuredExecution(
                value,
                Usage(requests=1, compute_units=9, concurrent_jobs=4),
                Decimal("1.20"),
                "USD",
            ),
        )
        self.assertEqual(result.text, "ok")
        self.assertEqual(result.usage, Usage(requests=1, compute_units=9, concurrent_jobs=4))
        self.assertEqual(len(self.plane.ledger()), 1)

    def test_brain_measurement_is_required(self):
        request = BrainControlRequest(
            request_id="brain-2",
            principal_id="owner-1",
            objective="decompose research",
            leaf_tasks=4,
            parallelism=2,
            estimated_cost=Decimal("1.00"),
            currency="USD",
            scopes=frozenset({"agent:run"}),
            available_providers=("local",),
        )
        with self.assertRaises(TypeError):
            self.adapter.execute(
                request,
                lambda route: {"provider": route["provider"], "text": "ok"},
                measure=lambda _value, _route: None,
            )
        self.assertEqual(self.plane.ledger(), ())
        self.assertEqual(self.plane.evidence(), ())


if __name__ == "__main__":
    unittest.main()
