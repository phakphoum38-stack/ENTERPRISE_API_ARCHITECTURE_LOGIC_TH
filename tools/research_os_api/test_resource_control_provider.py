from __future__ import annotations

from decimal import Decimal

import pytest

from .execution_contract import MeasuredExecution
from .resource_control_plane import ResourceControlPlane
from .resource_control_provider import ProviderControlRequest, ProviderResourceControlAdapter
from .resource_governance import Entitlement, QuotaDimension, Usage, Window
from .budgets import BudgetLimit


def _adapter() -> ProviderResourceControlAdapter:
    plane = ResourceControlPlane(api_key_pepper="test-pepper")
    plane.register_principal(
        "user-1",
        Entitlement(
            principal_id="user-1",
            scopes=frozenset({"agent:run"}),
            limits={(QuotaDimension.REQUESTS, Window.HOUR): 10},
            max_concurrency=2,
        ),
        BudgetLimit(currency="USD", amount=Decimal("10.00")),
    )
    plane.create_api_key(principal_id="user-1", scopes={"agent:run"})
    plane.add_policy_rule(effect="allow", scope="agent:run")
    return ProviderResourceControlAdapter(plane)


def test_provider_requires_measured_execution() -> None:
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

    with pytest.raises(TypeError, match="MeasuredExecution"):
        adapter.execute(
            request,
            provider_execute=lambda context: "raw-result",
            measure=lambda raw, context: raw,
        )


def test_provider_measured_execution_is_returned() -> None:
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
        usage=Usage(requests=1, tokens=12),
        cost=Decimal("0.12"),
        currency="USD",
    )

    result = adapter.execute(
        request,
        provider_execute=lambda context: {"text": "answer", "provider": context.provider},
        measure=lambda raw, context: measured,
    )

    assert result is measured
    assert result.currency == "USD"
    assert result.usage.tokens == 12


def test_provider_measurement_failure_releases_control_plane_reservation() -> None:
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

    with pytest.raises(TypeError):
        adapter.execute(
            request,
            provider_execute=lambda context: "raw-result",
            measure=lambda raw, context: object(),
        )

    assert adapter.control_plane.ledger() == ()
