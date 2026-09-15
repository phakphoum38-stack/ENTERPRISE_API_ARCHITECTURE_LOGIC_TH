"""Contract tests for the single-gate Friend -> Brain -> Factory -> Provider path."""
from decimal import Decimal
import unittest

from budgets import BudgetLimit
from execution_contract import MeasuredExecution
from resource_control_execution_pipeline import UnifiedExecutionRequest, UnifiedResourceExecutionPipeline
from resource_control_plane import ResourceControlPlane
from resource_governance import Entitlement, Limit, QuotaDimension, Usage, Window


class UnifiedResourceExecutionPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plane = ResourceControlPlane()
        self.plane.register_principal("owner-1", Entitlement("owner", scopes=frozenset({"agent:run"}), limits=(Limit(QuotaDimension.REQUESTS, Window.HOUR, 5), Limit(QuotaDimension.TOKENS, Window.HOUR, 20), Limit(QuotaDimension.COMPUTE_UNITS, Window.HOUR, 10)), max_concurrency=2), BudgetLimit("USD", Decimal("10.00")))
        self.pipeline = UnifiedResourceExecutionPipeline(self.plane)

    def test_complete_path_admits_once_and_preserves_stage_order(self) -> None:
        calls: list[str] = []
        request = UnifiedExecutionRequest("req-unified-1", "owner-1", "research architecture", Usage(requests=1, tokens=10, compute_units=2, concurrent_jobs=1), Decimal("1.00"), "USD", frozenset({"agent:run"}), ("local",), "research")
        def friend(req): calls.append("friend"); return {"objective": req.objective}
        def brain(req, friend_result): calls.append("brain"); return {"leaf_tasks": 2}
        def factory(req, brain_result): calls.append("factory"); return {"leaf_tasks": brain_result["leaf_tasks"], "plan": "test-plan"}
        def provider(context, factory_result): calls.append("provider"); return {"text": "answer", "provider": context.provider, "model": context.model}
        def measure(value, context):
            calls.append("measure")
            return MeasuredExecution(value, Usage(requests=1, tokens=8, compute_units=2, concurrent_jobs=1), Decimal("0.80"), "USD")
        result = self.pipeline.execute(request, friend=friend, brain=brain, factory=factory, provider=provider, measure=measure)
        self.assertEqual(calls, ["friend", "brain", "factory", "provider", "measure"])
        self.assertEqual(result.text, "answer")
        self.assertEqual(result.cost, Decimal("0.80"))
        self.assertEqual(len(self.plane.ledger()), 1)
        self.assertEqual(len(self.plane.evidence()), 1)

    def test_denied_admission_blocks_all_execution_stages(self) -> None:
        calls: list[str] = []
        plane = ResourceControlPlane()
        plane.register_principal("blocked-owner", Entitlement("blocked", scopes=frozenset({"agent:run"}), limits=(Limit(QuotaDimension.REQUESTS, Window.HOUR, 0),), max_concurrency=1), BudgetLimit("USD", Decimal("10.00")))
        pipeline = UnifiedResourceExecutionPipeline(plane)
        request = UnifiedExecutionRequest("req-denied-before-execution", "blocked-owner", "must not execute", Usage(requests=1), Decimal("1.00"), "USD", frozenset({"agent:run"}))
        result = pipeline.execute(request, friend=lambda _: calls.append("friend"), brain=lambda _, __: calls.append("brain"), factory=lambda _, __: calls.append("factory"), provider=lambda _, __: calls.append("provider"), measure=lambda _, __: calls.append("measure"))
        self.assertNotEqual(result.admission.decision.value, "allow")
        self.assertEqual(calls, [])
        self.assertEqual(len(plane.ledger()), 0)
        self.assertEqual(len(plane.evidence()), 0)

    def test_missing_measurement_fails_closed_before_accounting(self) -> None:
        request = UnifiedExecutionRequest("req-unified-2", "owner-1", "research architecture", Usage(requests=1, tokens=10, compute_units=1, concurrent_jobs=1), Decimal("1.00"), "USD", frozenset({"agent:run"}), (), "research")
        with self.assertRaises(TypeError):
            self.pipeline.execute(request, friend=lambda _: "friend", brain=lambda _, value: "brain", factory=lambda _, value: "factory", provider=lambda _, __: "unmeasured", measure=lambda value, context: value)
        self.assertEqual(len(self.plane.ledger()), 0)
        self.assertEqual(len(self.plane.evidence()), 0)


if __name__ == "__main__":
    unittest.main()
