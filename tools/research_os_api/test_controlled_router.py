"""Tests for admission-controlled runtime routing."""
from decimal import Decimal
import unittest

from agent_platform import AgentRegistry, AgentRouter
from admission import AdmissionDecision, ResourceAdmissionGate
from budgets import BudgetLedger, BudgetLimit
from controlled_router import GovernedAgentRouter
from policy import PolicyEffect, PolicyEngine, PolicyRule
from resource_governance import Entitlement, Limit, QuotaDimension, ResourceGovernance, Usage, Window


class GovernedAgentRouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.governance = ResourceGovernance()
        self.governance.register("user-1", Entitlement("pro", scopes=frozenset({"agent:run"}), limits=(Limit(QuotaDimension.REQUESTS, Window.HOUR, 10),), max_concurrency=2))
        self.policy = PolicyEngine()
        self.budget = BudgetLedger()
        self.budget.register("user-1", BudgetLimit("USD", Decimal("10.00")))
        self.gate = ResourceAdmissionGate(self.governance, self.policy, self.budget)
        self.registry = AgentRegistry()
        self.registry.register("general", providers=("local",))
        self.router = GovernedAgentRouter(self.gate, AgentRouter(self.registry))

    def route(self, *, requested_agent: str | None = None, idempotency_key: str | None = "k1", request_id: str = "req-1"):
        return self.router.route(
            request_id=request_id,
            principal_id="user-1",
            objective="answer the task",
            usage=Usage(requests=1, concurrent_jobs=1),
            estimated_cost=Decimal("2.00"),
            currency="USD",
            scopes=frozenset({"agent:run"}),
            idempotency_key=idempotency_key,
            requested_agent=requested_agent,
        )

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

    def test_idempotent_route_replay_fails_closed(self):
        first = self.route()
        second = self.route(request_id="retry")
        self.assertEqual(first.admission.decision, AdmissionDecision.ALLOW)
        self.assertEqual(second.admission.decision, AdmissionDecision.DENY)
        self.assertEqual(second.admission.reason, "idempotency_in_flight")
        self.assertIsNone(second.route)
        self.assertEqual(self.budget.snapshot("user-1")["reserved"], "2.00")


if __name__ == "__main__":
    unittest.main()