from __future__ import annotations

import unittest

from owner_special.research_os_friend.learning_executor_result import (
    LearningExecutorResultBoundary,
    LearningExecutorResultError,
    LearningExecutorResultRequest,
)


class LearningExecutorResultBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.boundary = LearningExecutorResultBoundary()
        self.activation = {
            "schema": "research-os-learning-skill-activation/v1",
            "activation_id": "activation-h24-001",
            "owner": "owner_special",
            "skill_name": "bounded-research",
            "skill_version": 1,
            "consumption_fingerprint": "a" * 64,
            "skill": {"name": "bounded-research", "procedure": ["inspect"]},
            "activation_state": "READY_FOR_H25",
            "execution_authority": "H25",
            "read_only": True,
            "authority": "none",
            "activation_fingerprint": "b" * 64,
            "correlation_id": "corr-h24",
        }
        self.request = LearningExecutorResultRequest(
            owner="owner_special",
            source_sha="c" * 40,
            skill_name="bounded-research",
            skill_version=1,
            activation_fingerprint="b" * 64,
            correlation_id="corr-h24",
            status="SUCCEEDED",
        )

    def test_success_result_is_classified(self) -> None:
        result = self.boundary.classify(self.request, self.activation, {"status": "SUCCEEDED", "output": "ok"})
        self.assertEqual(result["schema"], "research-os-learning-executor-result/v1")
        self.assertEqual(result["status"], "SUCCEEDED")
        self.assertEqual(result["evidence_authority"], "H26")
        self.assertTrue(result["read_only"])
        self.assertRegex(result["result_fingerprint"], r"^[0-9a-f]{64}$")

    def test_failed_and_blocked_statuses_are_allowed(self) -> None:
        for status in ("FAILED", "BLOCKED"):
            request = LearningExecutorResultRequest(
                owner=self.request.owner,
                source_sha=self.request.source_sha,
                skill_name=self.request.skill_name,
                skill_version=self.request.skill_version,
                activation_fingerprint=self.request.activation_fingerprint,
                correlation_id=self.request.correlation_id,
                status=status,
            )
            result = self.boundary.classify(request, self.activation, {"status": status, "reason": "bounded"})
            self.assertEqual(result["status"], status)

    def test_result_status_must_match_request(self) -> None:
        with self.assertRaises(LearningExecutorResultError):
            self.boundary.classify(self.request, self.activation, {"status": "FAILED"})

    def test_activation_mismatch_is_rejected(self) -> None:
        activation = dict(self.activation)
        activation["skill_version"] = 2
        with self.assertRaises(LearningExecutorResultError):
            self.boundary.classify(self.request, activation, {"status": "SUCCEEDED"})

    def test_invalid_status_is_rejected(self) -> None:
        request = LearningExecutorResultRequest(
            owner=self.request.owner,
            source_sha=self.request.source_sha,
            skill_name=self.request.skill_name,
            skill_version=1,
            activation_fingerprint=self.request.activation_fingerprint,
            correlation_id=self.request.correlation_id,
            status="PROMOTE",
        )
        with self.assertRaises(LearningExecutorResultError):
            self.boundary.classify(request, self.activation, {"status": "PROMOTE"})

    def test_unsafe_result_is_rejected(self) -> None:
        with self.assertRaises(LearningExecutorResultError):
            self.boundary.classify(self.request, self.activation, {"status": "SUCCEEDED", "output": "execute subprocess"})


if __name__ == "__main__":
    unittest.main()
