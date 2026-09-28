from __future__ import annotations

import unittest

from owner_special.research_os_friend.learning_lifecycle_boundary import (
    LearningLifecycleBoundary,
    LearningLifecycleError,
    LearningLifecycleRequest,
)

OWNER = "owner_special"
SOURCE_SHA = "a" * 40
CORRELATION = "corr-h16"
SKILL_FP = "b" * 64
RESULT_FP = "c" * 64


def result(status="SUCCEEDED", value=None) -> dict:
    return {
        "schema": "research-os-executor-result/v1",
        "owner": OWNER,
        "source_sha": SOURCE_SHA,
        "correlation_id": CORRELATION,
        "skill_fingerprint": SKILL_FP,
        "result_fingerprint": RESULT_FP,
        "status": status,
        "result": value or {"summary": "completed"},
        "read_only": True,
        "authority": "none",
    }


def request(status="SUCCEEDED", value=None) -> LearningLifecycleRequest:
    return LearningLifecycleRequest(
        owner=OWNER,
        source_sha=SOURCE_SHA,
        correlation_id=CORRELATION,
        skill_fingerprint=SKILL_FP,
        result_fingerprint=RESULT_FP,
        result_status=status,
        result=value or {"summary": "completed"},
    )


class LearningLifecycleBoundaryTests(unittest.TestCase):
    def test_successful_result_becomes_learned_state(self) -> None:
        output = LearningLifecycleBoundary().classify(request(), result())
        self.assertEqual(output["learning_state"], "LEARNED")
        self.assertTrue(output["read_only"])
        self.assertEqual(output["authority"], "none")

    def test_failed_and_blocked_states_are_preserved(self) -> None:
        boundary = LearningLifecycleBoundary()
        self.assertEqual(boundary.classify(request("FAILED"), result("FAILED"))["learning_state"], "FAILED")
        self.assertEqual(boundary.classify(request("BLOCKED"), result("BLOCKED"))["learning_state"], "BLOCKED")

    def test_identity_mismatch_fails_closed(self) -> None:
        with self.assertRaises(LearningLifecycleError):
            LearningLifecycleBoundary().classify(
                request(),
                {**result(), "source_sha": "d" * 40},
            )

    def test_result_fingerprint_mismatch_fails_closed(self) -> None:
        with self.assertRaises(LearningLifecycleError):
            LearningLifecycleBoundary().classify(request(), {**result(), "result_fingerprint": "d" * 64})

    def test_authority_violation_fails_closed(self) -> None:
        with self.assertRaises(LearningLifecycleError):
            LearningLifecycleBoundary().classify(request(), {**result(), "authority": "executor"})

    def test_unsafe_result_is_rejected(self) -> None:
        with self.assertRaises(LearningLifecycleError):
            LearningLifecycleBoundary().classify(
                request(value={"summary": "powershell"}),
                result(value={"summary": "powershell"}),
            )

    def test_snapshot_is_deterministic_and_detached(self) -> None:
        boundary = LearningLifecycleBoundary()
        first = boundary.classify(request(), result())
        first["result"]["summary"] = "mutated"
        second = boundary.classify(request(), result())
        self.assertEqual(second["result"]["summary"], "completed")
        self.assertEqual(first["lifecycle_fingerprint"], second["lifecycle_fingerprint"])


if __name__ == "__main__":
    unittest.main()
