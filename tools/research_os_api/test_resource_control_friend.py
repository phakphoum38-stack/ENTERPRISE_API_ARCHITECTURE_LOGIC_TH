"""Contract tests for the Friend-to-resource-control boundary."""
from decimal import Decimal
import os
import unittest

from budgets import BudgetLimit
from provider_measurement import ProviderMeasurement
from resource_control_friend import FriendControlRequest, FriendResourceControlAdapter
from resource_control_plane import ResourceControlPlane
from resource_governance import Entitlement, Limit, QuotaDimension, Usage, Window


class FakeFriendResult(dict):
    def __init__(
        self,
        *,
        provider: str,
        model: str,
        text: str,
        measurement: ProviderMeasurement,
    ) -> None:
        super().__init__(provider=provider, model=model, text=text)
        self.measurement = measurement



class FriendResourceControlTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ.setdefault("RESEARCH_OS_API_KEY_PEPPER", "test-friend-resource-control-pepper")
        self.plane = ResourceControlPlane()
        self.plane.register_principal(
            "owner-1",
            Entitlement(
                "owner",
                scopes=frozenset({"agent:run"}),
                limits=(Limit(QuotaDimension.REQUESTS, Window.HOUR, 10),),
                max_concurrency=2,
            ),
            BudgetLimit("USD", Decimal("10.00")),
        )
        self.adapter = FriendResourceControlAdapter(self.plane)

    def test_friend_execution_requires_measured_accounting(self):
        request = FriendControlRequest(
            request_id="friend-1",
            principal_id="owner-1",
            objective="research",
            usage=Usage(requests=1),
            estimated_cost=Decimal("1.00"),
            currency="USD",
            scopes=frozenset({"agent:run"}),
            available_providers=("local",),
        )

        with self.assertRaises(TypeError):
            self.adapter.execute(
                request,
                lambda route: {"provider": route["provider"], "text": "ok"},
            )

        self.assertEqual(self.plane.ledger(), ())
        self.assertEqual(self.plane.evidence(), ())
        self.assertEqual(self.plane.budget.snapshot("owner-1")["reserved"], "0")

    def test_friend_execution_commits_measured_result(self):
        request = FriendControlRequest(
            request_id="friend-2",
            principal_id="owner-1",
            objective="research",
            usage=Usage(requests=1, tokens=200),
            estimated_cost=Decimal("1.00"),
            currency="USD",
            scopes=frozenset({"agent:run"}),
            available_providers=("local",),
        )

        result = self.adapter.execute(
            request,
            lambda route: FakeFriendResult(
                provider="local",
                model=route["model"],
                text="ok",
                measurement=ProviderMeasurement(
                    usage=Usage(requests=1, tokens=200),
                    cost=Decimal("0.80"),
                    currency="USD",
                ),
            ),
        )

        self.assertEqual(result.text, "ok")
        self.assertEqual(result.usage, Usage(requests=1, tokens=200))
        self.assertEqual(result.cost, Decimal("0.80"))
        self.assertEqual(len(self.plane.ledger()), 1)
        self.assertEqual(len(self.plane.evidence()), 1)


if __name__ == "__main__":
    unittest.main()
