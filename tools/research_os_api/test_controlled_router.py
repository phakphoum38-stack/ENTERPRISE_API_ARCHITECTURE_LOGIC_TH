"""Tests for the admission-controlled runtime routing boundary."""
from decimal import Decimal
import unittest

from agent_platform import AgentRouter, AgentRegistry
from budgets import BudgetLedger, BudgetLimit
from controlled_router import GovernedAgentRouter
from admission import AdmissionDecision, ResourceAdmissionGate
from policy import PolicyEffect, PolicyEngine, PolicyRule
from resource_governance import Entitlement, Limit, QuotaDimension, ResourceGovernance, Usage, Window


class GovernedAgentRouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.governance = ResourceGovernance()
        self.governance.register(
            "user-1",
            Entitlement(
                "pro",
                scopes=frozenset({"agent:run"}),
                limits=(Limit(QuotaDimension.REQUESTS, Window.HOUR, 2),),
                max_concurrency=1,
            ),
        )
        self.policy = PolicyEngine()
        self.budget = BudgetLedger()
        self.budget.register("user-1", BudgetLimit("USD", Decimal("10.00")))
        gate = ResourceAdmissionGate(self.governance, self.policy, self.budget)
        self.router = GovernedAgentRouter(gate, AgentRouter(AgentRegistry()))

    def route(self, **overrides):
        values = {
            "request_id": "route-1",
            "principal_id": "user-1",
            "objective": "research and summarize",
            "usage": Usage(requests=1, concurrent_jobs=1),
            "estimated_cost": Decimal("2.00"),
            "currency": "USD",
            "scopes": frozenset({"agent:run"}),
            "idempotency_key": "route-key-1",
            "available_providers": ("local",),
        }
        values.update(overrides)
        return self.router.route(**values)

    def test_denied_admission_never_returns_runtime_route(self):
        self.policy.add_rule(PolicyRule("deny", PolicyEffect.DENY, required_scopes=frozenset({"agent:run"})))
        result = self.route(idempotency_key=None)
        self.assertEqual(result.admission.decision, AdmissionDecision.DENY)
        self.assertIsNone(result.route)

    def test_allowed_admission_returns_route_and_reservation(self):
        result = self.route()
        self.assertTrue(result.allowed)
        self.assertIsNotNone(result.route)
        self.assertTrue(result.admission.reservation_id)
        self.router.release(result.admission.reservation_id)

    def test_route_failure_releases_reservation(self):
        with self.assertRaises(ValueError):
            self.route(requested_agent="does-not-exist", idempotency_key=None)
        self.assertEqual(self.budget.snapshot("user-1")["reserved"], "0")

    def test_idempotent_route_reuses_admission(self):
        first = self.route()
        second = self.route()
        self.assertEqual(first.admission.reservation_id, second.admission.reservation_id)
        self.assertEqual(self.budget.snapshot("user-1")["reserved"], "2.00")


if __name__ == "__main__":
    unittest.main()
