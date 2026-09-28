from __future__ import annotations

import unittest

from owner_special.research_os_friend.self_learning.observation_pipeline import (
    LearningObservation,
    LearningObservationPipeline,
)
from owner_special.research_os_friend.self_learning.sandbox_test import SandboxTestBoundary
from owner_special.research_os_friend.self_learning.test_evidence import TestEvidenceBoundary


class TestEvidenceBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        pipeline = LearningObservationPipeline()
        pattern = pipeline.observe(
            LearningObservation(
                owner_id="owner-001",
                trigger="research-failure",
                outcome="validated-repair",
                evidence_refs=("EV-001",),
                context=(("project", "demo"),),
            )
        )
        candidate = pipeline.candidate(
            pattern,
            name="bounded-research",
            goal="reuse validated repair",
            procedure=("inspect", "validate"),
            evidence=("EV-001",),
            confidence=0.95,
        )
        self.result = SandboxTestBoundary().test(pipeline.sandbox(candidate))
        self.boundary = TestEvidenceBoundary()

    def test_passed_test_derives_deterministic_evidence(self) -> None:
        first = self.boundary.derive(self.result)
        second = self.boundary.derive(self.result)
        self.assertEqual(first, second)
        self.assertEqual(len(first.evidence_id), 64)
        self.assertEqual(len(first.result_hash), 64)
        self.assertEqual(first.test_id, self.result.test_id)
        self.assertTrue(first.passed)

    def test_evidence_binds_test_and_sandbox_lineage(self) -> None:
        evidence = self.boundary.derive(self.result)
        self.assertEqual(evidence.test_id, self.result.test_id)
        self.assertEqual(evidence.sandbox_id, self.result.sandbox_id)

    def test_malformed_test_identity_fails_closed(self) -> None:
        invalid = type(self.result)(
            test_id="invalid",
            sandbox_id=self.result.sandbox_id,
            passed=self.result.passed,
            checks=self.result.checks,
            failures=self.result.failures,
        )
        with self.assertRaises(ValueError):
            self.boundary.derive(invalid)

    def test_failed_test_remains_failed_evidence(self) -> None:
        failed = type(self.result)(
            test_id=self.result.test_id,
            sandbox_id=self.result.sandbox_id,
            passed=False,
            checks=(),
            failures=("sandbox_not_isolated",),
        )
        evidence = self.boundary.derive(failed)
        self.assertFalse(evidence.passed)
        self.assertEqual(evidence.test_id, failed.test_id)


if __name__ == "__main__":
    unittest.main()
