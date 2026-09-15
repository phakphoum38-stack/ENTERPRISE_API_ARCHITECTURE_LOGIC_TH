"""Integration tests for the single Research OS resource control plane."""
from decimal import Decimal
import unittest

from budgets import BudgetLimit
from execution_contract import MeasuredExecution
from resource_control_plane import ResourceControlPlane
from resource_governance import Entitlement, Limit, QuotaDimension, Usage, Window


class ResourceControlPlaneTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plane = ResourceControlPlane()
        self.plane.register_principal("user-1", Entitlement("pro", scopes=frozenset({"agent:run"}), limits=(Limit(QuotaDimension.REQUESTS, Window.HOUR, 10),), max_concurrency=2), BudgetLimit("USD", Decimal("10.00")))

    def test_execute_commits_measured_execution_and_evidence(self):
        result = self.plane.execute(request_id="req-1", principal_id="user-1", objective="research", usage=Usage(requests=1), estimated_cost=Decimal("2.00"), currency="USD", scopes=frozenset({"agent:run"}), available_providers=("local",), executor=lambda route: MeasuredExecution({"provider": route["provider"], "model": route["model"], "text": "ok"}, Usage(requests=1), Decimal("1.25"), "USD"))
        self.assertTrue(result.admission.allowed)
        self.assertEqual(result.text, "ok")
        self.assertEqual(result.cost, Decimal("1.25"))
        self.assertEqual(len(self.plane.ledger()), 1)
        self.assertEqual(len(self.plane.evidence()), 1)
        self.assertEqual(self.plane.evidence()[0]["ledger_hash"], self.plane.ledger()[0].entry_hash)

    def test_idempotency_replay_fails_closed_without_second_execution(self):
        calls: list[str] = []
        common = dict(principal_id="user-1", objective="once", usage=Usage(requests=1), estimated_cost=Decimal("1.00"), currency="USD", scopes=frozenset({"agent:run"}), available_providers=("local",), idempotency_key="same")
        first = self.plane.execute(request_id="first", executor=lambda route: calls.append("first") or MeasuredExecution({"provider": route["provider"], "model": route["model"], "text": "ok"}, Usage(requests=1), Decimal("0.50"), "USD"), **common)
        replay = self.plane.execute(request_id="retry", executor=lambda route: calls.append("retry") or MeasuredExecution({"text": "duplicate"}, Usage(requests=1), Decimal("0.50"), "USD"), **common)
        self.assertTrue(first.admission.allowed)
        self.assertFalse(replay.admission.allowed)
        self.assertEqual(replay.admission.reason, "idempotency_replay:committed")
        self.assertEqual(calls, ["first"])
        self.assertEqual(len(self.plane.ledger()), 1)
        self.assertEqual(len(self.plane.evidence()), 1)

    def test_invalid_measured_currency_releases_reservation(self):
        with self.assertRaises(ValueError):
            self.plane.execute(request_id="bad-currency", principal_id="user-1", objective="research", usage=Usage(requests=1), estimated_cost=Decimal("1.00"), currency="USD", scopes=frozenset({"agent:run"}), available_providers=("local",), executor=lambda route: MeasuredExecution({"text": "bad"}, Usage(requests=1), Decimal("1.00"), "EUR"))
        self.assertEqual(self.plane.ledger(), ())
        self.assertEqual(self.plane.evidence(), ())
        self.assertEqual(self.plane.budget.snapshot("user-1")["reserved"], "0")

    def test_unregistered_principal_fails_closed(self):
        with self.assertRaises(PermissionError):
            self.plane.admit(request_id="unknown", principal_id="missing", usage=Usage(requests=1), estimated_cost=Decimal("1.00"), currency="USD")


if __name__ == "__main__":
    unittest.main()
