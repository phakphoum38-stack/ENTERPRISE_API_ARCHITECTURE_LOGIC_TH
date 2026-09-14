"""Tests for the unified policy/quota/budget admission gate."""
from decimal import Decimal
from datetime import timedelta
import unittest

from admission import AdmissionDecision, AdmissionRequest, AdmissionStatus, ResourceAdmissionGate
from budgets import BudgetLedger, BudgetLimit
from policy import PolicyEffect, PolicyEngine, PolicyRule
from resource_governance import Entitlement, Limit, QuotaDimension, ResourceGovernance, Usage, Window


class ResourceAdmissionGateTests(unittest.TestCase):
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
        self.gate = ResourceAdmissionGate(self.governance, self.policy, self.budget)

    def request(self, *, key: str | None = "k1", requests: int = 1, cost: str = "2.00") -> AdmissionRequest:
        return AdmissionRequest(
            request_id="req-1",
            principal_id="user-1",
            usage=Usage(requests=requests, concurrent_jobs=1),
            estimated_cost=Decimal(cost),
            currency="USD",
            scopes=frozenset({"agent:run"}),
            idempotency_key=key,
        )

    def test_admission_reserves_quota_and_budget(self):
        result = self.gate.admit(self.request())
        self.assertEqual(result.decision, AdmissionDecision.ALLOW)
        self.assertTrue(result.reservation_id)
        self.assertEqual(self.governance.snapshot("user-1")["requests:hour:used"], 0)
        self.assertEqual(self.budget.snapshot("user-1")["reserved"], "2.00")

    def test_policy_deny_blocks_before_reservation(self):
        self.policy.add_rule(PolicyRule("deny-agents", PolicyEffect.DENY, required_scopes=frozenset({"agent:run"})))
        result = self.gate.admit(self.request(key=None))
        self.assertEqual(result.decision, AdmissionDecision.DENY)
        self.assertIn("policy_denied", result.reason)
        self.assertEqual(self.budget.snapshot("user-1")["reserved"], "0.00")

    def test_quota_and_budget_are_fail_closed(self):
        first = self.gate.admit(self.request(key="first", cost="9.00"))
        self.assertEqual(first.decision, AdmissionDecision.ALLOW)
        second = self.gate.admit(self.request(key="second", cost="2.00"))
        self.assertEqual(second.decision, AdmissionDecision.DENY)
        self.assertIn("budget", second.reason)
        self.gate.release(first.reservation_id)

    def test_idempotency_replays_same_reservation(self):
        first = self.gate.admit(self.request())
        second = self.gate.admit(self.request())
        self.assertEqual(first.reservation_id, second.reservation_id)
        self.assertEqual(self.budget.snapshot("user-1")["reserved"], "2.00")

    def test_idempotency_conflict_fails_closed(self):
        self.gate.admit(self.request())
        conflicting = AdmissionRequest(
            request_id="different",
            principal_id="user-1",
            usage=Usage(requests=1, concurrent_jobs=1),
            estimated_cost=Decimal("2.00"),
            currency="USD",
            scopes=frozenset({"agent:run"}),
            idempotency_key="k1",
        )
        result = self.gate.admit(conflicting)
        self.assertEqual(result.decision, AdmissionDecision.DENY)
        self.assertEqual(result.reason, "idempotency_conflict")

    def test_commit_records_actual_usage_and_cost(self):
        result = self.gate.admit(self.request())
        reservation = self.gate.commit(result.reservation_id, actual_usage=Usage(requests=1, concurrent_jobs=1), actual_cost=Decimal("1.25"))
        self.assertEqual(reservation.status, AdmissionStatus.COMMITTED)
        self.assertEqual(self.governance.snapshot("user-1")["requests:hour:used"], 1)
        self.assertEqual(self.budget.snapshot("user-1")["committed"], "1.25")
        self.assertEqual(self.budget.snapshot("user-1")["reserved"], "0")

    def test_release_returns_both_capacities(self):
        result = self.gate.admit(self.request())
        reservation = self.gate.release(result.reservation_id)
        self.assertEqual(reservation.status, AdmissionStatus.RELEASED)
        self.assertEqual(self.budget.snapshot("user-1")["reserved"], "0")

    def test_expired_admission_releases_budget(self):
        gate = ResourceAdmissionGate(self.governance, self.policy, self.budget, reservation_ttl=timedelta(seconds=1))
        result = gate.admit(self.request())
        reservation = gate.admit(AdmissionRequest(
            request_id="req-2",
            principal_id="user-1",
            usage=Usage(),
            estimated_cost=Decimal("0"),
            currency="USD",
        ), now=result.evaluated_at + timedelta(seconds=2))
        self.assertEqual(reservation.decision, AdmissionDecision.ALLOW)
        self.assertEqual(self.budget.snapshot("user-1")["reserved"], "0")

    def test_actual_usage_or_cost_above_reservation_fails(self):
        result = self.gate.admit(self.request())
        with self.assertRaisesRegex(ValueError, "exceeds reservation"):
            self.gate.commit(result.reservation_id, actual_usage=Usage(requests=2, concurrent_jobs=1))


if __name__ == "__main__":
    unittest.main()
