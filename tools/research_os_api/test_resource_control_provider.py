from __future__ import annotations

from decimal import Decimal
import os
import unittest

from budgets import BudgetLimit
from execution_contract import MeasuredExecution
from policy import PolicyEffect, PolicyRule
from resource_control_plane import ResourceControlPlane
from resource_control_provider import ProviderControlRequest, ProviderResourceControlAdapter
from resource_governance import Entitlement, Limit, QuotaDimension, Usage, Window


def _adapter() -> ProviderResourceControlAdapter:
    os.environ.setdefault("RESEARCH_OS_API_KEY_PEPPER", "test-provider-resource-control-pepper")
    plane = ResourceControlPlane()
    plane.register_principal(
        "user-1",
        Entitlement(
            "pro",
            scopes=frozenset({"agent:run"}),
            limits=(Limit(QuotaDimension.REQUESTS, Window.HOUR, 10),),
            max_concurrency=2,
        ),
        BudgetLimit("USD", Decimal("10.00")),
    )
    plane.add_policy_rule(
        PolicyRule(
            rule_id="provider-agent-run",
            effect=PolicyEffect.ALLOW,
            required_scopes=frozenset({"agent:run"}),
            principal_types=frozenset({"user"}),
        )
    )
    return ProviderResourceControlAdapter(plane)


class ProviderResourceControlTests(unittest.TestCase):
    def test_provider_requires_measured_execution(self) -> None:
        adapter = _adapter()
        request = ProviderControlRequest(
            request_id="provider-1",
            principal_id="user-1",
            objective="answer",
            provider="test-provider",
            model="test-model",
            estimated_usage=Usage(requests=1, tokens=10),
            estimated_cost=Decimal("0.10"),
            currency="usd",
        )

        with self.assertRaisesRegex(TypeError, "MeasuredExecution"):
            adapter.execute(
                request,
                provider_execute=lambda context: "raw-result",
                measure=lambda raw, context: raw,
            )

    def test_provider_measured_execution_is_committed(self) -> None:
        adapter = _adapter()
        request = ProviderControlRequest(
            request_id="provider-2",
            principal_id="user-1",
            objective="answer",
            provider="test-provider",
            model="test-model",
            estimated_usage=Usage(requests=1, tokens=10),
            estimated_cost=Decimal("0.10"),
            currency="USD",
        )
        measured = MeasuredExecution(
            value="answer",
            usage=Usage(requests=1, tokens=8),
            cost=Decimal("0.08"),
            currency="USD",
        )

        result = adapter.execute(
            request,
            provider_execute=lambda context: {"text": "answer", "provider": context.provider},
            measure=lambda raw, context: measured,
        )

        self.assertEqual(result.text, "answer")
        self.assertEqual(result.provider, "test-provider")
        self.assertEqual(result.model, "test-model")
        self.assertEqual(result.usage.tokens, 8)
        self.assertEqual(result.cost, Decimal("0.08"))
        self.assertEqual(result.currency, "USD")
        self.assertEqual(len(adapter.control_plane.ledger()), 1)

    def test_provider_measurement_failure_releases_control_plane_reservation(self) -> None:
        adapter = _adapter()
        request = ProviderControlRequest(
            request_id="provider-3",
            principal_id="user-1",
            objective="answer",
            provider="test-provider",
            model="test-model",
            estimated_usage=Usage(requests=1, tokens=10),
            estimated_cost=Decimal("0.10"),
            currency="USD",
        )

        with self.assertRaises(TypeError):
            adapter.execute(
                request,
                provider_execute=lambda context: "raw-result",
                measure=lambda raw, context: object(),
            )

        self.assertEqual(adapter.control_plane.ledger(), ())


if __name__ == "__main__":
    unittest.main()
