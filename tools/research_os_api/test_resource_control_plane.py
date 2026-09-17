"""Integration tests for the single Research OS resource control plane."""
from decimal import Decimal
import os
import unittest

from budgets import BudgetLimit
from execution_contract import MeasuredExecution
from resource_control_plane import ResourceControlPlane
from resource_governance import Entitlement, Limit, QuotaDimension, Usage, Window


class ResourceControlPlaneTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ.setdefault("RESEARCH_OS_API_KEY_PEPPER", "test-resource-control-plane-pepper")
        self.plane = ResourceControlPlane()
        self.plane.register_principal(
            "user-1",
            Entitlement(
                "pro",
                scopes=frozenset({"agent:run"}),
                limits=(Limit(QuotaDimension.REQUESTS, Window.HOUR, 10),),
                max_concurrency=2,
            ),
            BudgetLimit("USD", Decimal("10.00")),
        )

    def test_api_key_is_bound_to_registered_principal(self):
        record, raw = self.plane.create_api_key("user-1", {"agent:run"})
        verified = self.plane.authenticate(raw, required_scope="agent:run")
        self.assertEqual(record.key_id, verified.key_id)
        self.assertEqual(verified.principal_id, "user-1")

    def test_execute_commits_measured_execution(self):
        result = self.plane.execute(
            request_id="req-1",
            principal_id="user-1",
            objective="research and summarize",
            usage=Usage(requests=1, tokens=123, concurrent_jobs=1),
            estimated_cost=Decimal("2.00"),
            currency="USD",
            scopes=frozenset({"agent:run"}),
            available_providers=("local",),
            executor=lambda route: MeasuredExecution(
                {"provider": route["provider"], "model": route["model"], "text": "ok"},
                Usage(requests=1, tokens=123, concurrent_jobs=1),
                Decimal("1.25"),
                "usd",
            ),
        )
        self.assertEqual(result.admission.decision.value, "allow")
        self.assertEqual(result.text, "ok")
        self.assertEqual(result.usage, Usage(requests=1, tokens=123, concurrent_jobs=1))
        self.assertEqual(result.cost, Decimal("1.25"))
        self.assertEqual(result.currency, "USD")
        self.assertEqual(len(self.plane.ledger()), 1)
        self.assertEqual(len(self.plane.evidence()), 1)
        self.assertEqual(self.plane.evidence()[0]["ledger_hash"], self.plane.ledger()[0].entry_hash)

    def test_idempotency_prevents_duplicate_execution_while_first_is_reserved(self):
        calls: list[str] = []

        first = self.plane.execute(
            request_id="req-idempotent-first",
            principal_id="user-1",
            objective="research and summarize",
            usage=Usage(requests=1, concurrent_jobs=1),
            estimated_cost=Decimal("1.00"),
            currency="USD",
            scopes=frozenset({"agent:run"}),
            available_providers=("local",),
            idempotency_key="same-operation",
            executor=lambda route: (
                calls.append("first"),
                MeasuredExecution(
                    {"provider": route["provider"], "model": route["model"], "text": "ok"},
                    Usage(requests=1, concurrent_jobs=1),
                    Decimal("0.50"),
                    "USD",
                ),
            )[1],
        )
        self.assertEqual(first.admission.decision.value, "allow")

        second = self.plane.execute(
            request_id="req-idempotent-second",
            principal_id="user-1",
            objective="research and summarize",
            usage=Usage(requests=1, concurrent_jobs=1),
            estimated_cost=Decimal("1.00"),
            currency="USD",
            scopes=frozenset({"agent:run"}),
            available_providers=("local",),
            idempotency_key="same-operation",
            executor=lambda route: (
                calls.append("second"),
                MeasuredExecution(
                    {"provider": route["provider"], "model": route["model"], "text": "duplicate"},
                    Usage(requests=1, concurrent_jobs=1),
                    Decimal("0.50"),
                    "USD",
                ),
            )[1],
        )

        self.assertEqual(second.admission.decision.value, "deny")
        self.assertEqual(second.admission.reason, "idempotency_in_flight")
        self.assertEqual(calls, ["first"])
        self.assertEqual(len(self.plane.ledger()), 1)
        self.assertEqual(len(self.plane.evidence()), 1)

    def test_execution_failure_releases_reservation_and_writes_no_ledger(self):
        with self.assertRaises(RuntimeError):
            self.plane.execute(
                request_id="req-fail",
                principal_id="user-1",
                objective="research and summarize",
                usage=Usage(requests=1, concurrent_jobs=1),
                estimated_cost=Decimal("2.00"),
                currency="USD",
                scopes=frozenset({"agent:run"}),
                available_providers=("local",),
                executor=lambda _route: (_ for _ in ()).throw(RuntimeError("provider failed")),
            )
        self.assertEqual(self.plane.ledger(), ())
        self.assertEqual(self.plane.evidence(), ())
        self.assertEqual(self.plane.budget.snapshot("user-1")["reserved"], "0")

    def test_invalid_measured_currency_releases_reservation(self):
        with self.assertRaises(ValueError):
            self.plane.execute(
                request_id="req-currency",
                principal_id="user-1",
                objective="research and summarize",
                usage=Usage(requests=1, concurrent_jobs=1),
                estimated_cost=Decimal("2.00"),
                currency="USD",
                scopes=frozenset({"agent:run"}),
                available_providers=("local",),
                executor=lambda route: MeasuredExecution(
                    {"provider": route["provider"], "model": route["model"], "text": "bad"},
                    Usage(requests=1, concurrent_jobs=1),
                    Decimal("1.00"),
                    "EUR",
                ),
            )
        self.assertEqual(self.plane.ledger(), ())
        self.assertEqual(self.plane.evidence(), ())
        self.assertEqual(self.plane.budget.snapshot("user-1")["reserved"], "0")

    def test_evidence_and_ledger_form_hash_chains(self):
        for index in range(2):
            result = self.plane.execute(
                request_id=f"req-{index}",
                principal_id="user-1",
                objective="research and summarize",
                usage=Usage(requests=1, concurrent_jobs=0),
                estimated_cost=Decimal("1.00"),
                currency="USD",
                scopes=frozenset({"agent:run"}),
                available_providers=("local",),
                executor=lambda route: MeasuredExecution(
                    {"provider": route["provider"], "model": route["model"], "text": "ok"},
                    Usage(requests=1, concurrent_jobs=0),
                    Decimal("0.75"),
                    "USD",
                ),
            )
            self.assertTrue(result.ledger_entry)
            self.assertEqual(result.evidence["cost"], Decimal("0.75"))
        ledger = self.plane.ledger()
        evidence = self.plane.evidence()
        self.assertEqual(ledger[0].previous_hash, "0" * 64)
        self.assertEqual(ledger[1].previous_hash, ledger[0].entry_hash)
        self.assertEqual(evidence[0]["previous_hash"], "0" * 64)
        self.assertEqual(evidence[1]["previous_hash"], evidence[0]["evidence_hash"])
        self.assertEqual(self.plane.forensic_snapshot()["evidence_root"], evidence[-1]["evidence_hash"])

    def test_unregistered_principal_fails_closed(self):
        with self.assertRaises(PermissionError):
            self.plane.admit(
                request_id="unknown",
                principal_id="missing",
                usage=Usage(requests=1),
                estimated_cost=Decimal("1.00"),
                currency="USD",
            )


if __name__ == "__main__":
    unittest.main()
