from __future__ import annotations

import unittest

from owner_special.research_os_friend.self_learning.observation_pipeline import (
    LearningObservation,
    LearningObservationPipeline,
)
from owner_special.research_os_friend.self_learning.sandbox_test import (
    SandboxTestBoundary,
    SandboxTestSpecification,
)


class SandboxTestBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pipeline = LearningObservationPipeline()
        self.boundary = SandboxTestBoundary()

    def sandbox(self):
        pattern = self.pipeline.observe(
            LearningObservation(
                owner_id="owner-001",
                trigger="research-failure",
                outcome="validated-repair",
                evidence_refs=("EV-001",),
                context=(("project", "demo"),),
            )
        )
        candidate = self.pipeline.candidate(
            pattern,
            name="bounded-research",
            goal="reuse validated repair",
            procedure=("inspect", "validate"),
            evidence=("EV-001",),
            confidence=0.95,
        )
        return self.pipeline.sandbox(candidate)

    def test_valid_sandbox_passes_without_execution(self) -> None:
        result = self.boundary.test(self.sandbox())
        self.assertTrue(result.passed)
        self.assertEqual(
            result.checks,
            ("sandbox_isolated", "observation_lineage_bound", "procedure_declared"),
        )
        self.assertEqual(result.failures, ())

    def test_test_identity_is_deterministic(self) -> None:
        sandbox = self.sandbox()
        first = self.boundary.test(sandbox)
        second = self.boundary.test(sandbox)
        self.assertEqual(first, second)
        self.assertEqual(len(first.test_id), 64)

    def test_invalid_lineage_fails_closed(self) -> None:
        sandbox = self.sandbox()
        candidate = sandbox.candidate
        invalid = type(candidate)(
            name=candidate.name,
            goal=candidate.goal,
            procedure=candidate.procedure,
            evidence=candidate.evidence,
            confidence=candidate.confidence,
            status=candidate.status,
            version=candidate.version,
            metadata={"observation_fingerprint": "invalid"},
        )
        result = self.boundary.test(type(sandbox)(
            candidate=invalid,
            sandbox_id=sandbox.sandbox_id,
            isolated=True,
        ))
        self.assertFalse(result.passed)
        self.assertIn("missing_or_invalid_observation_lineage", result.failures)

    def test_specification_can_disable_individual_checks(self) -> None:
        sandbox = self.sandbox()
        result = self.boundary.test(
            sandbox,
            specification=SandboxTestSpecification(
                require_isolated=False,
                require_observation_lineage=False,
                require_nonempty_procedure=True,
            ),
        )
        self.assertTrue(result.passed)
        self.assertEqual(result.checks, ("procedure_declared",))


if __name__ == "__main__":
    unittest.main()
