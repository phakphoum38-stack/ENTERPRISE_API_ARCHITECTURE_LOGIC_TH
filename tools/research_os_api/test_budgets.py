"""Tests for economic budget accounting."""
from decimal import Decimal
import unittest

from budgets import BudgetDecision, BudgetLedger, BudgetLimit
from resource_governance import QuotaError


class BudgetLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = BudgetLedger()
        self.ledger.register("user-1", BudgetLimit("usd", Decimal("10.00")))

    def test_reservation_holds_budget(self) -> None:
        decision = self.ledger.reserve("user-1", Decimal("6.00"), currency="USD")
        self.assertEqual(decision.decision, BudgetDecision.ALLOW)
        snapshot = self.ledger.snapshot("user-1")
        self.assertEqual(snapshot["reserved"], "6.00")
        self.assertEqual(snapshot["remaining"], "4.00")

    def test_budget_exceeded_denies(self) -> None:
        self.ledger.reserve("user-1", Decimal("8.00"), currency="USD")
        decision = self.ledger.evaluate("user-1", Decimal("3.00"), currency="USD")
        self.assertEqual(decision.decision, BudgetDecision.DENY)
        self.assertEqual(decision.reason, "budget_exceeded")

    def test_commit_moves_reserved_to_committed(self) -> None:
        decision = self.ledger.reserve("user-1", Decimal("4.00"), currency="USD")
        reservation_id = next(iter(self.ledger._reservations))
        self.ledger.commit(reservation_id, actual=Decimal("3.50"))
        snapshot = self.ledger.snapshot("user-1")
        self.assertEqual(snapshot["committed"], "3.50")
        self.assertEqual(snapshot["reserved"], "0")
        self.assertEqual(decision.currency, "USD")

    def test_release_returns_capacity(self) -> None:
        self.ledger.reserve("user-1", Decimal("7.00"), currency="USD")
        reservation_id = next(iter(self.ledger._reservations))
        self.ledger.release(reservation_id)
        self.assertEqual(self.ledger.snapshot("user-1")["remaining"], "10.00")

    def test_currency_mismatch_fails_closed(self) -> None:
        with self.assertRaisesRegex(QuotaError, "currency mismatch"):
            self.ledger.evaluate("user-1", Decimal("1.00"), currency="EUR")

    def test_negative_and_non_finite_amounts_fail_closed(self) -> None:
        for amount in (Decimal("-1"), Decimal("NaN"), Decimal("Infinity")):
            with self.assertRaises(QuotaError):
                self.ledger.evaluate("user-1", amount, currency="USD")


if __name__ == "__main__":
    unittest.main()
