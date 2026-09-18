from __future__ import annotations

import unittest

from owner_special.research_os_friend.self_learning.evidence_confidence import (
    EvidenceConfidenceBoundary,
)
from owner_special.research_os_friend.self_learning.test_evidence import LearningEvidence


class EvidenceConfidenceBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.boundary = EvidenceConfidenceBoundary()

    def evidence(self, suffix: str, passed: bool) -> LearningEvidence:
        return LearningEvidence(
            evidence_id=(suffix * 64)[:64],
            test_id=("a" if suffix != "a" else "b") * 64,
            sandbox_id=f"sandbox-{suffix}",
            result_hash=("c" if suffix != "c" else "d") * 64,
            passed=passed,
        )

    def test_passed_evidence_derives_confidence(self) -> None:
        result = self.boundary.derive(self.evidence("a", True))
        self.assertEqual(result.passed_count, 1)
        self.assertEqual(result.evidence_count, 1)
        self.assertEqual(result.score, 1.0)
        self.assertEqual(result.status, "CONFIDENT")
        self.assertEqual(result.mathematical_root, "10^1000")
        self.assertEqual(result.coverage_model, "logical_cartesian_product")
        self.assertEqual(len(result.confidence_id), 64)

    def test_failed_evidence_cannot_increase_confidence(self) -> None:
        result = self.boundary.derive(self.evidence("b", False))
        self.assertEqual(result.score, 0.0)
        self.assertEqual(result.status, "HOLD")
        self.assertEqual(result.passed_count, 0)

    def test_aggregation_is_order_independent(self) -> None:
        first = self.evidence("a", True)
        second = self.evidence("c", True)
        self.assertEqual(
            self.boundary.aggregate((first, second)),
            self.boundary.aggregate((second, first)),
        )

    def test_malformed_evidence_fails_closed(self) -> None:
        invalid = LearningEvidence(
            evidence_id="invalid",
            test_id="a" * 64,
            sandbox_id="sandbox",
            result_hash="b" * 64,
            passed=True,
        )
        with self.assertRaises(ValueError):
            self.boundary.derive(invalid)

    def test_uppercase_and_non_sha_evidence_fail_closed(self) -> None:
        invalid = LearningEvidence(
            evidence_id="A" * 64,
            test_id="a" * 64,
            sandbox_id="sandbox",
            result_hash="b" * 64,
            passed=True,
        )
        with self.assertRaises(ValueError):
            self.boundary.derive(invalid)

    def test_mixed_evidence_is_bounded(self) -> None:
        result = self.boundary.aggregate(
            (self.evidence("a", True), self.evidence("b", False))
        )
        self.assertEqual(result.passed_count, 1)
        self.assertEqual(result.evidence_count, 2)
        self.assertEqual(result.score, 0.5)
        self.assertEqual(result.status, "CONFIDENT")

    def test_empty_evidence_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            self.boundary.aggregate(())


if __name__ == "__main__":
    unittest.main()
