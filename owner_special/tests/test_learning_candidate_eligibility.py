from __future__ import annotations

import unittest

from owner_special.research_os_friend.learning_candidate_eligibility import (
    LearningCandidateEligibilityBoundary,
    LearningCandidateEligibilityError,
    LearningCandidateEligibilityRequest,
)

OWNER = "owner_special"
SOURCE_SHA = "a" * 40
CORRELATION = "corr-h17"
SKILL_FP = "b" * 64
RESULT_FP = "c" * 64


def request(**overrides) -> LearningCandidateEligibilityRequest:
    values = {
        "owner": OWNER,
        "source_sha": SOURCE_SHA,
        "correlation_id": CORRELATION,
        "skill_fingerprint": SKILL_FP,
        "result_fingerprint": RESULT_FP,
    }
    values.update(overrides)
    return LearningCandidateEligibilityRequest(**values)


def lifecycle(status="SUCCEEDED", state="LEARNED", value=None, **overrides) -> dict:
    payload = {
        "schema": "research-os-learning-lifecycle/v1",
        "owner": OWNER,
        "source_sha": SOURCE_SHA,
        "correlation_id": CORRELATION,
        "skill_fingerprint": SKILL_FP,
        "result_fingerprint": RESULT_FP,
        "result_status": status,
        "learning_state": state,
        "result": value or {"name": "bounded research skill", "goal": "inspect trusted research context"},
        "read_only": True,
        "authority": "none",
    }
    payload.update(overrides)
    return payload


class LearningCandidateEligibilityTests(unittest.TestCase):
    def test_succeeded_learned_result_is_eligible(self) -> None:
        output = LearningCandidateEligibilityBoundary().evaluate(request(), lifecycle())
        self.assertTrue(output["eligible"])
        self.assertEqual(output["promotion_authority"], "H10")
        self.assertTrue(output["read_only"])
        self.assertEqual(output["authority"], "none")

    def test_failed_result_is_not_eligible(self) -> None:
        with self.assertRaises(LearningCandidateEligibilityError):
            LearningCandidateEligibilityBoundary().evaluate(request(), lifecycle("FAILED", "FAILED"))

    def test_blocked_result_is_not_eligible(self) -> None:
        with self.assertRaises(LearningCandidateEligibilityError):
            LearningCandidateEligibilityBoundary().evaluate(request(), lifecycle("BLOCKED", "BLOCKED"))

    def test_identity_mismatch_fails_closed(self) -> None:
        with self.assertRaises(LearningCandidateEligibilityError):
            LearningCandidateEligibilityBoundary().evaluate(request(), lifecycle(source_sha="d" * 40))

    def test_lifecycle_authority_violation_fails_closed(self) -> None:
        with self.assertRaises(LearningCandidateEligibilityError):
            LearningCandidateEligibilityBoundary().evaluate(request(), lifecycle(authority="promoter"))

    def test_unsafe_candidate_is_rejected(self) -> None:
        with self.assertRaises(LearningCandidateEligibilityError):
            LearningCandidateEligibilityBoundary().evaluate(
                request(), lifecycle(value={"name": "run subprocess"})
            )

    def test_snapshot_is_detached_and_deterministic(self) -> None:
        boundary = LearningCandidateEligibilityBoundary()
        first = boundary.evaluate(request(), lifecycle())
        first["candidate"]["name"] = "mutated"
        second = boundary.evaluate(request(), lifecycle())
        self.assertEqual(second["candidate"]["name"], "bounded research skill")
        self.assertEqual(first["eligibility_fingerprint"], second["eligibility_fingerprint"])


if __name__ == "__main__":
    unittest.main()
