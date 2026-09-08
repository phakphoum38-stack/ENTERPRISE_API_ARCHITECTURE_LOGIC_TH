from __future__ import annotations

import unittest

from owner_special.research_os_friend.executor_handoff_boundary import (
    ExecutorHandoffBoundary,
    ExecutorHandoffError,
    ExecutorHandoffRequest,
)


OWNER = "owner_special"
SOURCE_SHA = "a" * 40
CORRELATION = "corr-h14"
SKILL_FP = "b" * 64


def skill() -> dict:
    return {
        "name": "bounded research skill",
        "goal": "inspect trusted research context",
        "version": 1,
    }


def request(**overrides) -> ExecutorHandoffRequest:
    values = {
        "owner": OWNER,
        "source_sha": SOURCE_SHA,
        "correlation_id": CORRELATION,
        "skill_fingerprint": SKILL_FP,
        "activation_decision": "ALLOW_ACTIVATION",
        "capability": "LEARNED_SKILL_EXECUTOR",
    }
    values.update(overrides)
    return ExecutorHandoffRequest(**values)


class ExecutorHandoffBoundaryTests(unittest.TestCase):
    def test_allow_activation_produces_bounded_handoff(self) -> None:
        result = ExecutorHandoffBoundary().handoff(request(), skill())
        self.assertEqual(result["handoff"], "HANDOFF_READY")
        self.assertTrue(result["read_only"])
        self.assertEqual(result["authority"], "none")

    def test_inspection_cannot_be_upgraded_to_execution(self) -> None:
        with self.assertRaises(ExecutorHandoffError):
            ExecutorHandoffBoundary().handoff(
                request(activation_decision="ALLOW_INSPECTION"), skill()
            )

    def test_approval_required_cannot_be_handed_off(self) -> None:
        with self.assertRaises(ExecutorHandoffError):
            ExecutorHandoffBoundary().handoff(
                request(activation_decision="REQUIRE_APPROVAL"), skill()
            )

    def test_unsupported_capability_is_rejected(self) -> None:
        with self.assertRaises(ExecutorHandoffError):
            ExecutorHandoffBoundary().handoff(
                request(capability="SHELL_EXECUTOR"), skill()
            )

    def test_invalid_identity_is_rejected(self) -> None:
        with self.assertRaises(ExecutorHandoffError):
            ExecutorHandoffBoundary().handoff(
                request(owner="other_owner"), skill()
            )

    def test_unsafe_skill_is_rejected(self) -> None:
        unsafe = skill()
        unsafe["goal"] = "run subprocess"
        with self.assertRaises(ExecutorHandoffError):
            ExecutorHandoffBoundary().handoff(request(), unsafe)

    def test_handoff_is_detached_and_deterministic(self) -> None:
        boundary = ExecutorHandoffBoundary()
        first = boundary.handoff(request(), skill())
        first["skill"]["name"] = "mutated"
        second = boundary.handoff(request(), skill())
        self.assertEqual(second["skill"]["name"], "bounded research skill")
        self.assertEqual(first["handoff_fingerprint"], second["handoff_fingerprint"])


if __name__ == "__main__":
    unittest.main()
