from decimal import Decimal
import unittest

from budgets import BudgetLimit
from policy import PolicyRule
from resource_control_factory import FactoryWorkload, ResourceControlledFactory
from resource_control_plane import ResourceControlPlane
from resource_governance import Entitlement
from execution_contract import MeasuredExecution


class ResourceControlledFactoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plane = ResourceControlPlane()
        self.plane.register_principal(
            "factory-user",
            Entitlement("factory-user", frozenset({"agent:run"}), {"compute_units": 100, "requests": 10}, max_concurrency=4),
            BudgetLimit("USD", Decimal("10")),
        )
        self.plane.add_policy_rule(PolicyRule(
            effect="allow", scopes=frozenset({"agent:run"}), principal_types=frozenset({"user"})
        ))
        self.factory = ResourceControlledFactory(self.plane)

    def test_workload_maps_to_governed_usage(self):
        workload = FactoryWorkload(
            request_id="factory-1", principal_id="factory-user", objective="build",
            leaf_tasks=12, parallelism=3, scopes=frozenset({"agent:run"}),
        )
        usage = self.factory.reserve_usage(workload)
        self.assertEqual(usage.compute_units, 12)
        self.assertEqual(usage.concurrent_jobs, 3)
        self.assertEqual(usage.requests, 1)

    def test_execution_requires_measured_result(self):
        workload = FactoryWorkload(
            request_id="factory-2", principal_id="factory-user", objective="build",
            leaf_tasks=4, scopes=frozenset({"agent:run"}),
        )
        result = self.factory.execute(
            workload,
            lambda route: MeasuredExecution(
                {"text": "ok", "provider": "factory-test", "model": "test"},
                usage=self.factory.reserve_usage(workload),
                cost=Decimal("1.25"),
                currency="usd",
            ),
        )
        self.assertEqual(result.cost, Decimal("1.25"))
        self.assertEqual(result.currency, "USD")
        self.assertEqual(result.provider, "factory-test")
        self.assertEqual(len(self.plane.ledger()), 1)
        self.assertEqual(len(self.plane.evidence()), 1)

    def test_factory_failure_releases_reservation(self):
        workload = FactoryWorkload(
            request_id="factory-3", principal_id="factory-user", objective="build",
            leaf_tasks=2, scopes=frozenset({"agent:run"}),
        )
        with self.assertRaises(RuntimeError):
            self.factory.execute(workload, lambda route: (_ for _ in ()).throw(RuntimeError("boom")))
        self.assertEqual(len(self.plane.ledger()), 0)
        self.assertEqual(len(self.plane.evidence()), 0)


if __name__ == "__main__":
    unittest.main()
