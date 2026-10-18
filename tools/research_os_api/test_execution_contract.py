"""Tests for the measured execution boundary contract."""
from decimal import Decimal
import unittest

from execution_contract import ExecutionContext, MeasuredExecution
from resource_governance import Usage


class ExecutionContractTests(unittest.TestCase):
    def test_measured_execution_normalizes_currency(self):
        result = MeasuredExecution(
            value={"text": "ok"},
            usage=Usage(requests=1, tokens=12),
            cost=Decimal("1.25"),
            currency=" usd ",
        )
        self.assertEqual(result.currency, "USD")

    def test_measured_execution_rejects_negative_cost(self):
        with self.assertRaises(ValueError):
            MeasuredExecution(
                value=None,
                usage=Usage(requests=1),
                cost=Decimal("-0.01"),
                currency="USD",
            )

    def test_measured_execution_rejects_non_finite_cost_and_invalid_currency(self):
        for cost in (Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")):
            with self.assertRaisesRegex(ValueError, "finite Decimal"):
                MeasuredExecution(value=None, usage=Usage(requests=1), cost=cost, currency="USD")
        with self.assertRaisesRegex(ValueError, "three-letter code"):
            MeasuredExecution(value=None, usage=Usage(requests=1), cost=Decimal("0"), currency="US")
        with self.assertRaisesRegex(ValueError, "Usage instance"):
            MeasuredExecution(value=None, usage=None, cost=Decimal("0"), currency="USD")

    def test_execution_context_requires_identity_and_route_metadata(self):
        with self.assertRaises(ValueError):
            ExecutionContext("", "user-1", "mock", "model", {})
        with self.assertRaises(ValueError):
            ExecutionContext("req-1", "", "mock", "model", {})
        with self.assertRaises(ValueError):
            ExecutionContext("req-1", "user-1", "", "model", {})
        with self.assertRaises(ValueError):
            ExecutionContext("req-1", "user-1", "mock", "", {})

    def test_execution_context_is_immutable(self):
        context = ExecutionContext("req-1", "user-1", "mock", "model", {"agent": "research"})
        with self.assertRaises(Exception):
            context.request_id = "req-2"
