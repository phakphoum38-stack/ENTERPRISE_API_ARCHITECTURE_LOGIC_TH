"""Contract tests for the Friend-to-resource-control boundary."""
from decimal import Decimal
import unittest

from budgets import BudgetLimit
from execution_contract import MeasuredExecution
from provider_measurement import ProviderMeasurement
from resource_control_friend import FriendControlRequest, FriendResourceControlAdapter
from resource_control_plane import ResourceControlPlane
from resource_governance import Entitlement, Limit, QuotaDimension, Usage, Window


class FakeFriendResult(dict):
    def __init__(self, *, provider: str, model: str, text: str, measurement: ProviderMeasurement) -> None:
        super().__init__(provider=provider, model=model, text=text)
        self.measurement = measurement


class FriendResourceControlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plane = ResourceControlPlane()
        self.plane.register_principal("owner-1", Entitlement("owner", scopes=frozenset({"agent:run"}), limits=(Limit(QuotaDimension.REQUESTS, Window.HOUR, 10),), max_concurrency=2), BudgetLimit("USD", Decimal("10.00")))
        self.adapter = FriendResourceControlAdapter(self.plane)

    def test_friend_execution_requires_measured_accounting(self):
        request = FriendControlRequest("friend-1", "owner-1", "research", Usage(requests=1), Decimal("1.00"), "USD", frozenset({"agent:run"}), ("local",))
        with self.assertRaises(TypeError):
            self.adapter.execute(request, lambda _route: {"provider": "local", "text": "ok"}, measure=lambda _value, _route: {"not": "measured"})
        self.assertEqual(self.plane.ledger(), ())
        self.assertEqual(self.plane.evidence(), ())
        self.assertEqual(self.plane.budget.snapshot("owner-1")["reserved"], "0")

    def test_friend_execution_commits_measured_result(self):
        request = FriendControlRequest("friend-2", "owner-1", "research", Usage(requests=1, tokens=200), Decimal("1.00"), "USD", frozenset({"agent:run"}), ("local",))
        result = self.adapter.execute(request, lambda _route: {"provider": "local", "model": "friend", "text": "ok"}, measure=lambda value, _route: MeasuredExecution(value, Usage(requests=1, tokens=200), Decimal("0.80"), "USD"))
        self.assertEqual(result.text, "ok")
        self.assertEqual(result.usage, Usage(requests=1, tokens=200))
        self.assertEqual(result.cost, Decimal("0.80"))
        self.assertEqual(len(self.plane.ledger()), 1)
        self.assertEqual(len(self.plane.evidence()), 1)

    def test_friend_provider_measurement_is_authoritative(self):
        request = FriendControlRequest("friend-3", "owner-1", "research", Usage(requests=1, tokens=200), Decimal("1.00"), "USD", frozenset({"agent:run"}), ("local",))
        result = self.adapter.execute(
            request,
            lambda route: FakeFriendResult(
                provider="local",
                model="friend",
                text="ok",
                measurement=ProviderMeasurement(
                    usage=Usage(requests=1, tokens=150),
                    cost=Decimal("0.60"),
                    currency="USD",
                ),
            ),
        )
        self.assertEqual(result.usage, Usage(requests=1, tokens=150))
        self.assertEqual(result.cost, Decimal("0.60"))
        self.assertEqual(result.currency, "USD")

    def test_friend_provider_measurement_missing_cost_fails_closed(self):
        request = FriendControlRequest("friend-4", "owner-1", "research", Usage(requests=1), Decimal("1.00"), "USD", frozenset({"agent:run"}), ("local",))
        with self.assertRaises(ValueError):
            self.adapter.execute(
                request,
                lambda route: FakeFriendResult(
                    provider="local",
                    model="friend",
                    text="ok",
                    measurement=ProviderMeasurement(usage=Usage(requests=1)),
                ),
            )
        self.assertEqual(self.plane.ledger(), ())
        self.assertEqual(self.plane.budget.snapshot("owner-1")["reserved"], "0")


if __name__ == "__main__":
    unittest.main()
