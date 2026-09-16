"""Tests for the HTTP-to-control-plane adapter."""
from decimal import Decimal
import os
import unittest

from budgets import BudgetLimit
from execution_contract import ExecutionContext, MeasuredExecution
from provider_measurement import ProviderMeasurement
from resource_control_http import HTTPPrincipal, ResourceControlHTTPAdapter
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
                "requested_agent": "research",
            },
            self.principal,
            friend=lambda request: {"objective": request.objective},
            brain=lambda request, friend_result: {"leaf_tasks": 1},
            factory=lambda request, brain_result: {"plan": "http-test", "leaf_tasks": brain_result["leaf_tasks"]},
            provider=lambda context, factory_result: {
                "provider": context.provider,
                "model": context.model,
                "text": "ok",
            },
            measure=lambda value, context: MeasuredExecution(
                value,
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

    def test_execute_friend_uses_one_governance_boundary(self):
        calls: list[str] = []

        def friend(route: dict[str, object]) -> FakeFriendResult:
            calls.append("friend")
            return FakeFriendResult(
                provider="owner-mock",
                model="friend-unified-master",
                text="ok",
                measurement=ProviderMeasurement(
                    usage=Usage(requests=1),
                    cost=Decimal("0.01"),
                    currency="USD",
                ),
            )

        result = self.adapter.execute_friend(
            {
                "request_id": "req-friend",
                "objective": "hello",
                "usage": {"requests": 1},
                "estimated_cost": "0.01",
                "currency": "USD",
                "scopes": ["agent:run"],
                "available_providers": ["owner-mock"],
                "idempotency_key": "friend-op-1",
            },
            self.principal,
            friend_executor=friend,
        )

        self.assertEqual(result.admission.decision.value, "allow")
        self.assertEqual(calls, ["friend"])
        self.assertEqual(result.provider, "owner-mock")
        self.assertEqual(result.model, "friend-unified-master")
        self.assertEqual(result.text, "ok")
        self.assertEqual(result.usage, Usage(requests=1))
        self.assertEqual(len(self.plane.ledger()), 1)
        self.assertEqual(len(self.plane.evidence()), 1)

    def test_execute_friend_denial_blocks_friend(self):
        calls: list[str] = []
        plane = ResourceControlPlane()
        plane.register_principal(
            "blocked-user",
            Entitlement(
                "blocked",
                scopes=frozenset({"agent:run"}),
                limits=(Limit(QuotaDimension.REQUESTS, Window.HOUR, 0),),
                max_concurrency=1,
            ),
            BudgetLimit("USD", Decimal("10.00")),
        )
        adapter = ResourceControlHTTPAdapter(plane)
        principal = HTTPPrincipal("blocked-user", frozenset({"agent:run"}))

        result = adapter.execute_friend(
            {
                "request_id": "req-friend-denied",
                "objective": "must not run",
                "usage": {"requests": 1},
                "estimated_cost": "0.01",
                "currency": "USD",
                "scopes": ["agent:run"],
            },
            principal,
            friend_executor=lambda route: calls.append("friend"),
        )

        self.assertEqual(result.admission.decision.value, "deny")
        self.assertEqual(calls, [])
        self.assertEqual(len(plane.ledger()), 0)
        self.assertEqual(len(plane.evidence()), 0)

    def test_execute_friend_idempotency_replay_executes_once(self):
        calls: list[str] = []
        body = {
            "request_id": "req-first",
            "objective": "once",
            "usage": {"requests": 1},
            "estimated_cost": "0.01",
            "currency": "USD",
            "scopes": ["agent:run"],
            "idempotency_key": "same-operation",
        }

        first = self.adapter.execute_friend(
            body,
            self.principal,
            friend_executor=lambda route: calls.append("friend") or FakeFriendResult(
                provider="owner-mock",
                model="friend",
                text="ok",
                measurement=ProviderMeasurement(
                    usage=Usage(requests=1),
                    cost=Decimal("0.01"),
                    currency="USD",
                ),
            ),
        )
        replay_body = {**body, "request_id": "req-replay"}
        replay = self.adapter.execute_friend(
            replay_body,
            self.principal,
            friend_executor=lambda route: calls.append("replay") or FakeFriendResult(
                provider="owner-mock",
                model="friend",
                text="should-not-run",
                measurement=ProviderMeasurement(
                    usage=Usage(requests=1),
                    cost=Decimal("0.01"),
                    currency="USD",
                ),
            ),
        )

        self.assertEqual(first.admission.decision.value, "allow")
        self.assertEqual(replay.admission.decision.value, "deny")
        self.assertEqual(replay.admission.reason, "idempotency_replay:committed")
        self.assertEqual(calls, ["friend"])
        self.assertEqual(len(self.plane.ledger()), 1)
        self.assertEqual(len(self.plane.evidence()), 1)


if __name__ == "__main__":
    unittest.main()
